"""Container for Printer."""
from ara.graph import ABBType, CFType, Graph, CFGView

from .option import Option, String, Choice, Bool, Graph_Type
from .step import Step

import pydot
import os.path

import graph_tool.draw


class Printer(Step):
    """Print graphs to dot."""

    SHAPES = {
        ABBType.computation: ("oval", "", "blue"),
        ABBType.call: ("box", "", "red"),
        ABBType.syscall: ("box", "rounded", "green")
    }

    def _fill_options(self):
        self.dot = Option(name="dot",
                          help="Path to a dot file, '-' will write to stdout.",
                          step_name=self.get_name(),
                          ty=String())
        self.graph_name = Option(name="graph_name",
                                 help="Name of the graph.",
                                 step_name=self.get_name(),
                                 ty=String())
        self.subgraph = Option(name="subgraph",
                               help="Choose, what subgraph should be printed.",
                               step_name=self.get_name(),
                               ty=Choice("abbs", "instances", "sstg"))
        self.graph = Option(name="graph",
                               help="Graph object of sstg.",
                               step_name=self.get_name(),
                               ty=Graph_Type())
        self.opts += [self.dot, self.graph_name, self.subgraph, self.graph]

    def _print_init(self):
        dot = self.dot.get()
        if not dot:
            self._fail("dot file path must be given.")

        name = self.graph_name.get()
        if not name:
            name = ''
        return name

    def _write_dot(self, dot):
        dot_path = self.dot.get()
        assert dot_path
        dot_path = os.path.abspath(dot_path)
        os.makedirs(os.path.dirname(dot_path), exist_ok=True)
        dot.write(dot_path)
        self._log.info(f"Write {self.subgraph.get()} to {dot_path}.")

    def print_abbs(self, g):
        name = self._print_init()

        dot_graph = pydot.Dot(graph_type='digraph', label=name)
        for function in g.cfg.vertices():
            if not g.cfg.vp.is_function[function]:
                continue
            dot_func = pydot.Cluster(g.cfg.vp.name[function],
                                     label=g.cfg.vp.name[function])
            dot_graph.add_subgraph(dot_func)
            for edge in function.out_edges():
                if g.cfg.ep.type[edge] != CFType.f2a:
                    continue
                abb = edge.target()
                if g.cfg.vp.type[abb] == ABBType.not_implemented:
                    assert not g.cfg.vp.implemented[function]
                    dot_abb = pydot.Node(str(hash(abb)),
                                         label="",
                                         shape="box")
                    dot_func.set('style', 'filled')
                    dot_func.set('color', '#eeeeee')
                else:
                    dot_abb = pydot.Node(
                        str(hash(abb)),
                        label=g.cfg.vp.name[abb],
                        shape=self.SHAPES[g.cfg.vp.type[abb]][0],
                        style=self.SHAPES[g.cfg.vp.type[abb]][1],
                        color=self.SHAPES[g.cfg.vp.type[abb]][2]
                    )
                dot_func.add_node(dot_abb)
        for edge in g.cfg.edges():
            if g.cfg.ep.type[edge] not in [CFType.lcf, CFType.icf]:
                continue
            color = "black"
            if g.cfg.ep.type[edge] == CFType.lcf:
                color = "red"
            if g.cfg.ep.type[edge] == CFType.icf:
                color = "blue"
            dot_graph.add_edge(pydot.Edge(str(hash(edge.source())),
                                          str(hash(edge.target())),
                                          color=color))
        self._write_dot(dot_graph)

    def print_instances(self, g):
        name = self._print_init()

        dot_graph = pydot.Dot(graph_type='digraph', label=name)
        for instance in g.instances.vertices():
            dot_node = pydot.Node(
                str(hash(instance)),
                label=g.instances.vp.label[instance],
            )
            dot_graph.add_node(dot_node)
        for edge in g.instances.edges():
            dot_graph.add_edge(pydot.Edge(str(hash(edge.source())),
                                          str(hash(edge.target())),
                                          label=g.instances.ep.label[edge]))
        self._write_dot(dot_graph)

    def print_sstg(self, g):
        sstg = self.graph.get()
        if not sstg:
            self._fail("Graph must be given when choosing sstg.")
        
        name = self._print_init()
        dot_graph = pydot.Dot(graph_type='digraph', label=name)
        
        cfg = CFGView(g.cfg, efilt=lambda x: g.cfg.ep.type[x] == CFType.icf or g.cfg.ep.type[x] == CFType.lcf)

        # print all vertices
        for state_node in sstg.vertices():
            state = sstg.vp.state[state_node]
            dot_node = pydot.Node(
                str(hash(state_node)),
                label=state.__repr__()
            )
            dot_graph.add_node(dot_node)
        
        # print all edges
        for edge in sstg.edges():
            color = "black"

            # look for important edges and color them red
            # s_state = sstg.vp.state[edge.source()]
            # t_state = sstg.vp.state[edge.target()]

            # for cpu in s_state.activated_tasks:
            #     s_task = s_state.get_scheduled_task(cpu)
            #     t_task = t_state.get_scheduled_task(cpu)
            #     if s_task is not None and t_task is not None and s_task.name != t_task.name:
            #         t_abb = t_state.abbs[t_task.name]
            #         s_abb = s_state.abbs[s_task.name]
            #         if t_abb not in cfg.vertex(s_abb).out_neighbors():
            #           color = "red"

            dot_graph.add_edge(pydot.Edge(
                str(hash(edge.source())),
                str(hash(edge.target())),
                color=color
            ))

        self._write_dot(dot_graph)

    def run(self, g: Graph):
        subgraph = self.subgraph.get()
        if subgraph == 'abbs':
            self.print_abbs(g)
        if subgraph == 'instances':
            self.print_instances(g)
        if subgraph == 'sstg':
            self.print_sstg(g)
