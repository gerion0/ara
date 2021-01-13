"""Container for SSE step."""
import graph_tool
import copy
import functools
import json

import pyllco

from ara.graph import (ABBType, Graph, CFGView, CFType, CallPath,
                       SyscallCategory, InstanceGraph as _InstanceGraph)
from .step import Step
from .option import Option, String, Bool
from ara.os.freertos import Task
from ara.os.zephyr import Thread, ISR
from ara.util import VarianceDict

from collections import defaultdict
from itertools import chain
from graph_tool.topology import (dominator_tree, label_out_component,
                                 all_paths, all_circuits)




class State:
    def __init__(self, cfg=None, callgraph=None, next_abbs=None):
        self.cfg = cfg
        self.callgraph = callgraph
        if not next_abbs:
            next_abbs = []
        self.next_abbs = next_abbs

        self.instances = _InstanceGraph()
        self.call_path = None # call node within the call graph
        self.branch = False # is this state coming from a branch
        self.loop = False # is this state coming from a loop
        self.running = None # what instance (Task or ISR) is currently running

    def __repr__(self):
        ret = f'State(Branch: {self.branch}, Loop: {self.loop} '
        abbs = [self.cfg.vp.name[abb] for abb in self.next_abbs]
        ret += ', '.join(abbs)
        ret += ", CallPath: " + self.call_path.print(call_site=True)
        return ret + ')'

    def copy(self):
        scopy = State()
        scopy.instances = self.instances.copy()
        scopy.call_path = copy.copy(self.call_path)
        for key, value in self.__dict__.items():
            if key in ['instances', 'call_path']:
                continue
            setattr(scopy, key, value)
        return scopy


class FlowAnalysis(Step):
    """Base class for all flow analyses.

    Apply the base SSE state search to the CFG. Can be specialized with some
    interface functions.
    """

    entry_point = Option(name="entry_point",
                         help="system entry point",
                         ty=String())
    stats = Option(name="stats",
                   help="Output stats file (Respects dump_prefix).",
                   ty=Bool())

    def new_vertex(self, sstg, state):
        vertex = sstg.add_vertex()
        sstg.vp.state[vertex] = state
        return vertex

    def _get_os_specific_deps(self):
        if self._graph.os is None:
            return ['SysFuncts']
        return self._graph.os.get_special_steps()

    def _require_instances(self):
        if self._graph.os is None:
            return ['SysFuncts']
        deps = self._graph.os.get_special_steps()
        if self._graph.os.has_dynamic_instances():
            deps.append('InstanceGraph')
        return deps

    def _system_semantic(self, state):
        new_states = self._execute(state)
        self._schedule(new_states)
        return new_states

    def run(self):
        entry_label = self.entry_point.get()
        if not entry_label:
            self._fail("Entry point must be given.")
        self._log.info(f"Analyzing entry point: '{entry_label}'")

        self._step_data = self._get_step_data(set)

        self._stats = { "name": entry_label }

        self._cfg = self._graph.cfg
        self._icfg = CFGView(self._graph.cfg, efilt=self._graph.cfg.ep.type.fa == CFType.icf)
        self._lcfg = CFGView(self._graph.cfg, efilt=self._graph.cfg.ep.type.fa == CFType.lcf)

        self._entry_func = entry_label

        self._init_analysis()

        sstg = graph_tool.Graph()
        sstg.vertex_properties["state"] = sstg.new_vp("object")

        state_vertex = self.new_vertex(sstg, self._get_initial_state())

        stack = [state_vertex]

        counter = 0
        while stack:
            self._log.debug(f"Round {counter:3d}, "
                            f"Stack with {len(stack)} state(s): "
                            f"{[sstg.vp.state[v] for v in stack]}")
            state_vertex = stack.pop()
            state = sstg.vp.state[state_vertex]
            for n in self._system_semantic(state):
                new_state = self.new_vertex(sstg, n)
                sstg.add_edge(state_vertex, new_state)
                stack.append(new_state)
            counter += 1
        self._log.info(f"Analysis needed {counter} iterations.")

        self._stats["iterations"] = counter

        self._finish(sstg)

        stats = self.stats.get()
        if stats:
            uuid = self._step_manager.get_execution_id()
            stat_file = f'{uuid}.{entry_label}.statistics.json'
            stat_file = self.dump_prefix.get() + stat_file

            with open(stat_file, 'w') as f:
                json.dump(self._stats, f, indent=4)


class MultiState:
    def __init__(self, cfg=None, instances=None):
        self.cfg = cfg
        self.instances = instances
        self.abbs = {}
        self.min_time = 0
        self.max_time = 0

    def __repr__(self):
        ret = ""
        for abb in self.abbs.values():
            if abb is not None:
                ret += self.cfg.vp.name[abb] + ", "
        return ret

    def copy(self):
        scopy = MultiState()

        for key, value in self.__dict__.items():
            if key == 'instances' or key == 'abbs':
                continue
            setattr(scopy, key, value)
        scopy.instances = self.instances.copy()
        scopy.abbs = self.abbs.copy()
        return scopy

class MultiSSE(FlowAnalysis):
    """Run the MultiCore SSE."""
    def get_single_dependencies(self):
        return self._require_instances()

    def _init_analysis(self):
        pass

    def _get_initial_state(self):
        self.print_tasks()
        state = MultiState(cfg=self._graph.cfg,
                           instances=self._graph.instances)

        #building initial state
        func_name_start = "AUTOSAR_TASK_FUNC_"
        for v in state.instances.vertices():
            task = state.instances.vp.obj[v]
            if task.autostart:
                func_name = func_name_start + task.name
                entry_func = self._graph.cfg.get_function_by_name(func_name)
                entry_abb = self._graph.cfg.get_entry_abb(entry_func)
                if task.cpu_id not in state.abbs:
                    state.abbs[task.cpu_id] = entry_abb
        return state

    def _execute(self, state):
        self._log.info(f"Executing State: {state}")
        new_states = []

        for cpu, abb in state.abbs.items():
            if abb is not None:
                # syscall handling
                if self._icfg.vp.type[abb] == ABBType.syscall:
                    assert self._graph.os is not None
                    new_state = self._graph.os.interpret(self._graph.cfg, abb, state)
                    new_states.append(new_state)

                # handling calls and computations blocks the same way atm
                else:
                    for n in self._icfg.vertex(abb).out_neighbors():
                        new_state = state.copy()
                        new_state.abbs[cpu] = n
                        new_states.append(new_state)
        return new_states

    def _schedule(self, states):
        return []

    def _finish(self, sstg):
        pass

    def print_tasks(self):
        log = "Tasks ("
        instances = self._graph.instances
        for vertex in instances.vertices():
            task = instances.vp.obj[vertex]
            log += task.name + ", "
        self._log.info(f"{log})")


class FlatAnalysis(FlowAnalysis):
    """Analysis that run one time over the control flow reachable from the
    entry point.

    This analysis does not respect loops.
    """
    def _init_analysis(self):
        self._call_graph = self._graph.callgraph
        self._cond_func = {}
        self._loop_func = {}
        self._step_data.add(self._entry_func)

        self._visited = defaultdict(lambda: defaultdict(lambda: False))
        self._max_call_depth = 0

    def _get_initial_state(self):
        # find main
        entry_func = self._graph.cfg.get_function_by_name(self._entry_func)
        entry_abb = self._graph.cfg.get_entry_abb(entry_func)

        entry = State(cfg=self._graph.cfg,
                      callgraph=self._graph.callgraph,
                      next_abbs=[entry_abb])

        self._graph.os.init(entry)

        entry.call_path = CallPath()
        entry.scheduler_on = self._is_chained_analysis(self._entry_func)
        instance = self._find_running_instance(self._entry_func)
        entry.running = instance
        if instance:
            entry.branch = self._graph.instances.vp.branch[instance]
            entry.loop = self._graph.instances.vp.loop[instance]

        return entry

    # TODO: Move into OS model
    def _iterate_tasks(self):
        """Return a generator over all tasks in self._graph.instances."""
        if self._graph.instances is None:
            return
        for v in self._graph.instances.vertices():
            os_obj = self._graph.instances.vp.obj[v]
            if (isinstance(os_obj, Task) and os_obj.is_regular or
                    isinstance(os_obj, Thread) or isinstance(os_obj, ISR)):
                yield os_obj, v

    def _get_task_function(self, task):
        """Return the function which defines a task."""
        assert task.entry_abb is not None, "Not a regular Task."
        entry = self._graph.cfg.vertex(task.entry_abb)
        return self._graph.cfg.get_function(entry)

    def _find_running_instance(self, entry_func):
        for task, v in self._iterate_tasks():
            func = self._get_task_function(task)
            if self._graph.cfg.vp.name[func] == entry_func:
                return v
        return None

    def _is_chained_analysis(self, entry_func):
        return self._find_running_instance(entry_func) is not None

    def _init_execution(self, state):
        pass

    def _init_fake_state(self, state, abb):
        pass

    def _evaluate_fake_state(self, state, abb):
        pass

    def _handle_call(self, old_state, new_state, abb):
        pass

    def _is_bad_call_target(self, abb):
        return False

    def _get_categories(self):
        return SyscallCategory.every

    def _get_call_node(self, call_path, abb):
        """Return the call node for the given abb, respecting the call_path."""
        edge = self._call_graph.get_edge_for_callsite(abb)
        if edge is None:
            self._fail(f"Cannot find call path for ABB {abb_name}.")
        new_call_path = copy.copy(call_path)
        new_call_path.add_call_site(self._call_graph, edge)
        return new_call_path

    def _execute(self, state):
        new_states = []
        self._init_execution(state)
        for abb in state.next_abbs:
            # don't handle already visited vertices
            if self._visited[state.call_path][abb]:
                continue
            self._visited[state.call_path][abb] = True
            self._log.debug(f"Handle state {state}")
            call_depth = len(state.call_path)
            if self._max_call_depth < call_depth:
                self._max_call_depth = call_depth

            # syscall handling
            if self._icfg.vp.type[abb] == ABBType.syscall:
                name = self._icfg.vp.name[abb]
                syscall_name = self._cfg.get_syscall_name(abb)
                self._log.debug(f"Handle syscall: {name} ({syscall_name})")
                fake_state = state.copy()
                self._init_fake_state(fake_state, abb)
                assert self._graph.os is not None
                new_state = self._graph.os.interpret(
                    self._graph.cfg, abb, fake_state,
                    categories=self._get_categories()
                )
                self._evaluate_fake_state(new_state, abb)
                new_states.append(new_state)

            # call handling
            elif self._icfg.vp.type[abb] == ABBType.call:
                func = self._cfg.vp.name[self._cfg.get_function(abb)]
                self._log.debug(f"Handle call: {self._icfg.vp.name[abb]} to {func}")
                handled = False
                for n in self._icfg.vertex(abb).out_neighbors():
                    if self._is_bad_call_target(n):
                        continue
                    new_call_path = self._get_call_node(state.call_path, abb)
                    if new_call_path.is_recursive():
                        self._log.debug(f"Found recursive function. Callpath {new_call_path}")
                        continue
                    new_state = state.copy()
                    new_state.next_abbs = [n]
                    new_state.call_path = new_call_path
                    self._handle_call(state, new_state, abb)
                    new_states.append(new_state)
                    handled = True
                # if only recursive functions are found, handle the call like a
                # normal computation block
                if not handled:
                    for n in self._lcfg.vertex(abb).out_neighbors():
                        new_state = state.copy()
                        new_state.next_abbs = [n]
                        new_states.append(new_state)

            # exit handling
            elif (self._icfg.vp.is_exit[abb] and
                  self._icfg.vertex(abb).out_degree() > 0):
                self._log.debug(f"Handle exit: {self._icfg.vp.name[abb]}")
                new_state = state.copy()
                callsite = new_state.call_path[-1]
                call = new_state.callgraph.ep.callsite[callsite]
                neighbors = self._lcfg.vertex(call).out_neighbors()
                new_state.next_abbs = [next(neighbors)]
                new_state.call_path.pop_back()
                new_states.append(new_state)

            # computation block handling
            else:
                self._log.debug(f"Handle computation: {self._icfg.vp.name[abb]}")
                for n in self._icfg.vertex(abb).out_neighbors():
                    new_state = state.copy()
                    new_state.next_abbs = [n]
                    new_states.append(new_state)

        return new_states

    def _schedule(self, state):
        # we do simply not care
        return

    def _finish(self, sstg):
        self._log.info(f"Maximal call depth: {self._max_call_depth}")
        self._stats["maximal_call_depth"] = self._max_call_depth
        if self.dump.get():
            uuid = self._step_manager.get_execution_id()
            dot_file = f'{uuid}.{self._entry_func}.dot'
            dot_file = self.dump_prefix.get() + dot_file
            self._step_manager.chain_step({"name": "Printer",
                                           "dot": dot_file,
                                           "graph_name": 'Instances',
                                           "subgraph": 'instances'})

instance_graph_first_exec: bool = True
class InstanceGraph(FlatAnalysis):
    """Find all application instances."""

    def _get_entry_point_dep(self, name):
        return {"name": name, "entry_point": self.entry_point.get()}

    def get_single_dependencies(self):
        deps = self._get_os_specific_deps()
        deps += list(map(self._get_entry_point_dep,
                         ["Syscall", "ValueAnalysis"]))
        return deps

    def _init_analysis(self):
        super()._init_analysis()
        self._new_entry_points = set()
        # TODO: Move into OS model after rebase
        global instance_graph_first_exec
        if instance_graph_first_exec:
            for v in self._graph.instances.vertices():
                instance = self._graph.instances.vp.obj[v]
                if isinstance(instance, Thread):
                    self._step_manager.chain_step({"name": "InstanceGraph", "entry_point":
                        instance.entry_name})
                    self._step_data.add(instance.entry_name)
            instance_graph_first_exec = False

    def _dominates(self, dom_tree, abb_x, abb_y):
        """Does abb_x dominate abb_y?"""
        while abb_y:
            if abb_x == abb_y:
                return True
            abb_y = dom_tree[abb_y]
        return False

    def _has_path(self, graph, source, target):
        ap = all_paths(graph, graph.vertex(source), graph.vertex(target))
        try:
            next(ap)
            return True
        except StopIteration:
            return False

    @functools.lru_cache(maxsize=32)
    def _get_func_cfg(self, func):
        """Get LCFG of function"""
        abb = self._cfg.get_entry_abb(func)
        comp = label_out_component(self._lcfg, self._lcfg.vertex(abb))
        return CFGView(self._lcfg, vfilt=comp)

    @functools.lru_cache(maxsize=32)
    def _create_dom_tree(self, func):
        """Create a dominator tree of the local control flow for func."""
        func_cfg = self._get_func_cfg(func)
        entry = self._cfg.get_entry_abb(func)

        # prepare LCFG, endless loops are filtered out and replaces by exit
        # blocks
        exit_map = func_cfg.vp.is_exit.copy(full=False)
        keep_edge_map = func_cfg.new_ep("bool", val=True)

        loops = CFGView(func_cfg, vfilt=func_cfg.vp.is_exit_loop_head)
        for v in loops.vertices():
            v = func_cfg.vertex(v)
            for e in v.in_edges():
                if self._has_path(func_cfg, v, e.source()):
                    keep_edge_map[e] = False
                    exit_map[e.source()] = True

        patched_func_cfg = CFGView(func_cfg, efilt=keep_edge_map)

        # dom tree creation
        dom_tree = dominator_tree(patched_func_cfg,
                                  patched_func_cfg.vertex(entry))
        return dom_tree, CFGView(func_cfg, vfilt=exit_map)

    def _is_in_condition(self, abb):
        """Is abb part of a condition?"""
        func = self._graph.cfg.get_function(abb)
        dom_tree, exit_abbs = self._create_dom_tree(func)
        return not all([self._dominates(dom_tree, abb, x)
                       for x in exit_abbs.vertices()])

    def _is_in_loop(self, abb):
        """Is abb part of a loop?"""
        return self._cfg.vp.part_of_loop[abb]

    def _init_fake_state(self, state, abb):
        state.branch = (self._cond_func.get(state.call_path, False) or
                        self._is_in_condition(abb))
        state.loop = (self._loop_func.get(state.call_path, False) or
                      self._is_in_loop(abb))

    def _extract_entry_points(self):
        for task, _ in self._iterate_tasks():
            if (task not in self._new_entry_points):
                func_name = self._graph.cfg.vp.name[self._get_task_function(task)]
                if func_name not in self._step_data:
                    # order is different here, the first chained step will
                    # be the last executed one
                    self._step_manager.chain_step({"name": self.get_name(),
                                                   "entry_point": func_name})
                    self._step_data.add(func_name)
                self._new_entry_points.add(task)

    def _evaluate_fake_state(self, new_state, abb):
        self._graph.instances = new_state.instances
        self._extract_entry_points()

    def _init_execution(self, state):
        if self._graph.instances is not None:
            state.instances = self._graph.instances

    def _handle_call(self, old_state, new_state, abb):
        new_state.branch = (self._cond_func.get(old_state.call_path, False) or
                            self._is_in_condition(abb))
        self._cond_func[new_state.call_path] = new_state.branch

        new_state.loop = (self._loop_func.get(old_state.call_path, False) or
                          self._is_in_loop(abb))
        self._loop_func[new_state.call_path] = new_state.loop

    def _get_categories(self):
        return SyscallCategory.create

    def _is_bad_call_target(self, abb):
        cfg = self._graph.cfg
        cg = self._graph.callgraph
        cg_vertex = cg.vertex(cfg.vp.call_graph_link[cfg.get_function(abb)])
        return not cg.vp.syscall_category_create[cg_vertex]

    def _finish(self, sstg):
        super()._finish(sstg)
        self._log.debug(f"_get_func_cfg {self._get_func_cfg.cache_info()}")
        self._log.debug(f"_create_dom_tree {self._create_dom_tree.cache_info()}")


class InteractionAnalysis(FlatAnalysis):
    """Find the flow insensitive interactions between instances."""

    def get_single_dependencies(self):
        return self._require_instances()

    def _init_analysis(self):
        super()._init_analysis()
        self._chain_entry_points()

    def _chain_entry_points(self):
        for task, _ in self._iterate_tasks():
            func_name = self._graph.cfg.vp.name[self._get_task_function(task)]
            if func_name not in self._step_data:
                self._step_manager.chain_step({"name": self.get_name(),
                                               "entry_point": func_name})
                self._step_data.add(func_name)

    def _get_categories(self):
        return SyscallCategory.comm

    def _evaluate_fake_state(self, new_state, abb):
        self._graph.instances = new_state.instances

    def _init_execution(self, state):
        if self._graph.instances is not None:
            state.instances = self._graph.instances
