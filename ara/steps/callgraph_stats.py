# SPDX-FileCopyrightText: 2021 Jan Neugebauer
# SPDX-FileCopyrightText: 2023 Gerion Entrup <entrup@sra.uni-hannover.de>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Container for CFGStats."""
from .step import Step
from .util import open_with_dirs

from graph_tool.topology import min_spanning_tree, pseudo_diameter
from graph_tool import GraphView

import json


class CallGraphStats(Step):
    """Gather statistics about the Control Flow Graph."""

    def get_single_dependencies(self):
        return ["CallGraph"]

    def run(self):
        # TODO convert to StatsStep, see SSTGStats
        callgraph = self._graph.callgraph

        num_functions = callgraph.num_vertices()
        num_callees = callgraph.num_edges()

        # maximal call depth
        max_cd = 0
        for syscall in callgraph.get_syscalls().vertices():
            rev = GraphView(callgraph, reversed=True)
            mst = GraphView(
                rev, efilt=min_spanning_tree(rev, root=rev.vertex(syscall)))
            dist, ends = pseudo_diameter(mst, source=mst.vertex(syscall))
            max_cd = max([max_cd, int(dist) - 1])

        self._log.info(f"Number of function: {num_functions}")
        self._log.info(f"Number of callees: {num_callees}")
        self._log.info(f"Maximum call path depth: {max_cd}")

        if self.dump.get():
            with open_with_dirs(self.dump_prefix.get() + '.json', 'w') as f:
                values = {"num_functions": num_functions,
                          "num_callees": num_callees,
                          "max_path_depth": max_cd}
                json.dump(values, f, indent=4)
