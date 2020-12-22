import ara.steps.py_logging

def provide_steps():
    from .step import provide_steps as _native_provide
    from .abb_merge import ABBMerge
    from .callgraph_stats import CallGraphStats
    from .cfg_optimize import CFGOptimize
    from .cfg_stats import CFGStats
    from .dummy import Dummy
    from .generator import Generator
    from .icfg import ICFG
    from .load_oil import LoadOIL
    from .manual_corrections import ManualCorrections
    from .printer import Printer
    from .sse import InstanceGraph, InteractionAnalysis, MultiSSE
    from .syscall import Syscall
    from .sysfuncts import SysFuncts
    from .system_relevant_functions import SystemRelevantFunctions
    from .zephyr_static_post import ZephyrStaticPost

    for step in _native_provide():
        yield step

    yield ABBMerge
    yield CallGraphStats
    yield CFGOptimize
    yield CFGStats
    yield Dummy
    yield Generator
    yield ICFG
    yield InstanceGraph
    yield InteractionAnalysis
    yield LoadOIL
    yield Printer
    yield ManualCorrections
    yield MultiSSE
    yield Syscall
    yield SysFuncts
    yield SystemRelevantFunctions
    yield ZephyrStaticPost
