#!/usr/bin/env python3.6

import json
import stepmanager
import graph
import sys

from native_step import Step


def main():
    g = graph.PyGraph()
    os_name = sys.argv[1]
    json_file = sys.argv[2]
    i_file = sys.argv[3]
    print("Testing with", i_file, "and json:", json_file, "and os: ", os_name)
    with open(json_file) as f:
        data = json.load(f)

    config = {'os': os_name,
              'input_files': [i_file]}
    p_manager = stepmanager.StepManager(g, config)

    p_manager.execute(['ValidationStep'])

    abbs = g.get_type_vertices("ABB")
    for abb in abbs:
        if (abb is not None and abb.get_name() in data and
                not abb.get_loop_information()):
            print("abb has no loop information: ", abb.get_name())
            sys.exit(1)


if __name__ == '__main__':
    main()
