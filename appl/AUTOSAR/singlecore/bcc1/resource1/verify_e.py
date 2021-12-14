from generator.analysis.verifier_tools import *

def after_SystemStateFlow(analysis):
    # Find all three systemcall handlers
    (H1, H2, H3, H4, H5, Idle, StartOS) = \
       get_functions(analysis.system_graph, ["H1", "H2", "H3", "H4", "H5",
                                       "Idle", "StartOS"])
    (RES_SCHEDULER, R345) = get_objects(analysis.system_graph, ["RES_SCHEDULER", "R345"])

    t = RunningTaskToolbox(analysis)

    t.reachability(StartOS, "StartOS", [], # =>
                   [H5])

    t.reachability(H5, "ActivateTask", [H4], # =>
                   [H5])
    t.reachability(H5, "ActivateTask", [H3], # =>
                   [H5])
    t.reachability(H5, "ActivateTask", [H2], # =>
                   [H2])
    t.reachability(H5, "ActivateTask", [H1], # =>
                   [H1])


    t.reachability(H5, "ReleaseResource", [R345], # =>
                   [H3])

    t.reachability(H1, "TerminateTask", [], # =>
                   [H5])
    t.reachability(H2, "TerminateTask", [], # =>
                   [H5])
    t.reachability(H3, "TerminateTask", [], # =>
                   [H4])
    t.reachability(H4, "TerminateTask", [], # =>
                   [H5])
    t.reachability(H5, "TerminateTask", [], # =>
                   [Idle])


    t.reachability(Idle, "Idle", [], # =>
         [Idle])

    t.promise_all_syscalls_checked()
