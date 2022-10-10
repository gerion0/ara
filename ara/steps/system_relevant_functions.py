"""Container for SystemRelevantFunction."""
from ara.graph import SyscallCategory
from .step import Step

from graph_tool import GraphView
from graph_tool.topology import label_out_component
from .option import Option, Bool


class SystemRelevantFunctions(Step):
    """Mark all function that are in the Callgraph as system relevant or not."""

    no_stubs = Option(name="no_stubs",
                          help="Do not mark system functions that are declared as stub. "
                               "This can increase the performance of the analysis if you have many stubs in your OS model. "
                               "Set this option also for the SysFuncts step or set the commandline argument --no-stubs.",
                          ty=Bool(),
                          default_value=False)

    def get_single_dependencies(self):
        return ["CallGraph", "SysFuncts"]

    def run(self):
        if self._graph.os is None:
            self._log.warn("No OS detected. This step is meaningless then.")
            return

        callgraph = self._graph.callgraph

        every_set = {SyscallCategory.every, }

        # begin with syscalls, they are always entry points
        for syscall, sys_func in self._graph.os.syscalls.items():
            if self.no_stubs.get() and sys_func.is_stub:
                continue
            for sys_cat in every_set | sys_func.categories:
                cg_node = callgraph.get_node_with_name(syscall)
                if cg_node is None:
                    continue

                gv = GraphView(callgraph, reversed=True)
                # TODO: triggers a SEGFAULT
                # old_sys_rel = gv.copy_property(gv.vp.system_relevant)
                # gv.set_vertex_filter(old_sys_rel, inverted=True)
                vprop = callgraph.vp["syscall_category_" + sys_cat.name]
                label_out_component(gv, cg_node, label=vprop)

        if self.dump.get():
            self._step_manager.chain_step(
                {"name": "Printer",
                    "dot": self.dump_prefix.get() + 'dot',
                    "graph_name": 'System relevant functions',
                    "subgraph": 'callgraph'}
            )
