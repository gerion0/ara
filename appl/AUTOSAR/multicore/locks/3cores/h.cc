/**
 * @defgroup apps Applications
 * @brief The applications...
 */

/**
 * @file
 * @ingroup apps
 * @brief Just a simple test application
 */
#include "autosar/os.h"
#include "test/test.h"
#include "machine.h"


// TODO: wie geht das für multicore?
#if TRACE_JSON
{
  "vertices": [
  ],
  "edges": [
  ]
}
#endif //TRACE_JSON

#if LOCKS_JSON
{"no_timing": {"spin_states": {"S1": 2, "S2": 0}}}
#endif //LOCKS_JSON





DeclareTask(T01);
DeclareTask(T11);
DeclareTask(T21);
DeclareSpinlock(S1);
DeclareSpinlock(S2);

TEST_MAKE_OS_MAIN( StartOS(0) )

TASK(T01) {
	ActivateTask(T11);
	GetSpinlock(S1);
	ReleaseSpinlock(S1);
	TerminateTask();
}

TASK(T11) {
	ActivateTask(T21);
	GetSpinlock(S1);
	ReleaseSpinlock(S1);
	TerminateTask();
}

TASK(T21) {
	TerminateTask();
}

