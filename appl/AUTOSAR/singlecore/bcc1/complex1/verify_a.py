from generator.analysis.verifier_tools import *

def after_SystemStateFlow(analysis):
    # Find all three systemcall handlers
    (H1, H2, H3, Idle, StartOS, ISR1) = \
       get_functions(analysis.system_graph, ["H1", "H2", "H3", "Idle", "StartOS", "ISR1"])

    t = RunningTaskToolbox(analysis)
    t.mark_syscalls_in_function(H3)
    t.mark_syscalls_in_function(ISR1)

    t.reachability(StartOS, "StartOS", [], # =>
         [Idle])

    t.reachability(H2, "TerminateTask", [], # =>
         [Idle])

    t.reachability(H1, "TerminateTask", [], # =>
         [H2, # Activated by Alarm
          Idle,
         ])

    t.activate([Idle, H1], # =>
               H2)

    t.reachability(Idle, "Idle", [], # =>
         [Idle])

    t.promise_all_syscalls_checked()
