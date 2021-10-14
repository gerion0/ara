from generator.analysis.verifier_tools import *

def after_CurrentRunningSubtask(analysis):
    (Handler11,  bar) = \
       get_functions(analysis.system_graph, ["Handler11", "bar"])

    # bar belongs to Handler11
    assert bar.subtask == Handler11
    # And is already moved to the Task of Handler11
    assert bar in Handler11.task.functions

def after_SystemStateFlow(analysis):
    # Find all three systemcall handlers
    (Handler11, Handler12, Handler13, bar, Idle, StartOS) = \
       get_functions(analysis.system_graph, ["Handler11", "Handler12", "Handler13", "bar", "Idle", "StartOS"])

    t = RunningTaskToolbox(analysis)

    # Handler11 has higher priority than Handler12
    t.reachability(StartOS, "StartOS", [], # =>
         [Handler11])

    # Handler13 is directly started
    t.reachability(Handler11, "ChainTask", [Handler13], # =>
         [Handler13])

    # bar is called by Handler11
    t.reachability(bar, "ActivateTask", [Handler12], # =>
         [Handler11])


    # Handler 13 does always lead to the activated handler 12
    t.reachability(Handler13, "TerminateTask", [], # =>
         [Handler12, Idle])

    # Handler12 is always activated afterwards
    t.reachability(Handler12, "TerminateTask", [], # =>
         [Idle])

    # Idle handler is never left
    t.reachability(Idle, "Idle", [], # =>
         [Idle])

    t.promise_all_syscalls_checked()
