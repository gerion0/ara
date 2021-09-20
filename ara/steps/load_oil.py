"""Container for OilStep."""
import json

import ara.graph as _graph
from .option import Option, String
from .step import Step
from ara.os.autosar import (Task, Counter, Alarm, AlarmAction, ISR, Event,
                            TASK_PREFIX)
from ara.os.os_base import TaskStatus

import functools

DISABLE_ALARMS = True
DISABLE_ISRS = True


class LoadOIL(Step):
    """Reads an oil file and writes all information to the graph.

    Expect the path to the oil file to be in the config 'oilfile' key.
    The syntax is changed to JSON. Take a look at tests/oil/1.oil.
    """
    oilfile = Option(name="oilfile",
                     help="Path to JSON oil file.",
                     ty=String())

    def get_single_dependencies(self):
        return ["LLVMMap", "SVFAnalyses"]

    def run(self):
        cfg = self._graph.cfg

        from ara.steps import get_native_component
        ValueAnalyzer = get_native_component("ValueAnalyzer")
        va = ValueAnalyzer(self._graph)

        # load the json file
        oilfile = self.oilfile.get()
        if not oilfile:
            self.fail("No oilfile provided")
        self._log.info(f"Reading oil file {oilfile}")
        with open(oilfile) as f:
            oil = json.load(f)

        # RegisterTaskEntry needs the ABBs of all Tasks (they will be created
        # as dependency of the Syscall step), so put it at the end by
        # requesting it first
        self._step_manager.chain_step({"name": "RegisterTaskEntry"})

        instances = self._graph.instances
        for cpu in oil["cpus"]:
            cpu_id = cpu["id"]

            # read all tasks
            for task in cpu["tasks"]:
                t = instances.add_vertex()
                t_name = task["name"]
                t_func_name = "AUTOSAR_TASK_FUNC_" + t_name
                t_func = cfg.get_function_by_name(t_func_name)
                # Use a fake ABB, since we don't have real ones yet.
                # Leave this to the RegisterTaskEntry step
                self._log.debug(f"Found Task {t_name}")
                instances.vp.obj[t] = Task(cfg=cfg,
                                           name=t_name,
                                           function=t_func,
                                           priority=task["priority"],
                                           activation=task["activation"],
                                           autostart=task["autostart"],
                                           schedule=task["schedule"],
                                           cpu_id=cpu_id)
                instances.vp.is_control[t] = True
                instances.vp.label[t] = t_name

                # assign object to the concrete code
                code_instance = va.find_global(TASK_PREFIX + t_name)
                if code_instance is not None:
                    va.assign_system_object(code_instance, instances.vp.obj[t])

                # trigger other steps
                self._step_manager.chain_step({"name": "Syscall",
                                               "entry_point": t_func_name})

        @functools.lru_cache(maxsize=8)
        def find_instance_by_name(name, _class):
            obj = None
            for v in instances.vertices():
                obj = instances.vp.obj[v]
                if isinstance(obj, _class):
                    if obj.name == name:
                        return obj

            self.fail("Couldn't find instance with name " + name)

        for cpu in oil["cpus"]:
            cpu_id = cpu["id"]

            # read all counters
            for counter in cpu["counters"]:
                c = instances.add_vertex()
                instances.vp.obj[c] = Counter(counter["name"],
                                              cpu_id,
                                              counter["mincycle"],
                                              counter["maxallowedvalue"],
                                              counter["ticksperbase"],
                                              counter["secondspertick"])
                instances.vp.label[c] = counter["name"]

            # read all alarms
            if DISABLE_ALARMS:
                cpu["alarms"] = []

            for alarm in cpu["alarms"]:
                a = instances.add_vertex()
                instances.vp.label[a] = alarm["name"]

                counter = find_instance_by_name(alarm["counter"], Counter)

                # read alarm action
                action = alarm["action"]
                if action["action"].lower() == "incrementcounter":
                    incrcounter = find_instance_by_name(action["counter"],
                                                        Counter)
                    instances.vp.obj[a] = Alarm(alarm["name"],
                                                cpu_id,
                                                counter,
                                                alarm["autostart"],
                                                AlarmAction.INCREMENTCOUNTER,
                                                incrementcounter=incrcounter)
                elif action["action"].lower() == "activatetask":
                    task = find_instance_by_name(action["task"], Task)
                    instances.vp.obj[a] = Alarm(alarm["name"],
                                                cpu_id,
                                                counter,
                                                alarm["autostart"],
                                                AlarmAction.ACTIVATETASK,
                                                task=task)
                elif action["action"].lower() == "setevent":
                    task = find_instance_by_name(action["task"], Task)
                    event = find_instance_by_name(action["event"], Event)
                    instances.vp.obj[a] = Alarm(alarm["name"],
                                                cpu_id,
                                                counter,
                                                alarm["autostart"],
                                                AlarmAction.SETEVENT,
                                                task=task,
                                                event=event)

                # set cycletime and alarmtime if autostart is true
                if instances.vp.obj[a].autostart:
                    instances.vp.obj[a].cycletime = alarm["cycletime"]
                    instances.vp.obj[a].alarmtime = alarm["alarmtime"]

            # read all ISRs
            if DISABLE_ISRS:
                cpu["isrs"] = []

            for isr in cpu["isrs"]:
                i = instances.add_vertex()
                instances.vp.label[i] = isr["name"]

                i_function_name = "AUTOSAR_ISR_" + isr["name"]
                i_function = g.cfg.get_function_by_name(i_function_name)

                group = []
                for name in isr["group"]:
                    task = find_instance_by_name(name, Task)
                    group.append(task)

                instances.vp.obj[i] = ISR(i_function_name,
                                          cpu_id,
                                          isr["category"],
                                          isr["priority"],
                                          i_function,
                                          group)

                # trigger other steps
                self._step_manager.chain_step({"name": "Syscall",
                                                "entry_point": i_function_name})

        self._log.debug("find_instance_by_name "
                        f"{find_instance_by_name.cache_info()}")

        if self.dump.get():
            self._step_manager.chain_step({"name": "Printer",
                                           "dot": self.dump_prefix.get() + "instances.dot",
                                           "graph_name": 'Instances',
                                           "subgraph": 'instances'})
