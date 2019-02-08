"""Manages all steps."""
from typing import List

import steps
import graph


class StepManager:
    """Manages all steps.

    Knows about all steps and can execute them in correct order.
    Usage: Construct one instance of StepManager and then call execute()
    with a list of step that should be executed.
    """

    def __init__(self, g: graph.PyGraph, config: dict,
                 provides=steps.provide_steps):
        """Construct a StepManager.

        Arguments:
        g      -- the system graph
        config -- the program configuration. This should be a dict.

        Keyword arguments:
        provides -- An optional provides function to announce the passes to
                    StepManager
        """
        self._graph = g
        self._config = config
        self._steps = {}
        for step in provides(config):
            self._steps[step.get_name()] = step

    def get_step(self, name):
        """Get the step with specified name or None."""
        return self._steps.get(name, None)

    def get_steps(self):
        """Get all available steps as set."""
        return set(self._steps.values())

    def execute(self, esteps: List[str]):
        """Executes all steps in correct order.

        Arguments:
        esteps -- list of steps to execute. The elements are strings that
                  matches the ones returned by step.get_name().
        """
        # TODO transform this into a graph data structure
        # this is really quick and dirty
        for step in esteps:
            for dep in self._steps[step].get_dependencies():
                esteps.append(dep)

        execute = []

        for step in reversed(esteps):
            if step not in execute:
                print("Steps to run:", step)
                execute.append(step)

        for step in execute:
            self._steps[step].run(self._graph)
