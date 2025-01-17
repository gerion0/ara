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

typedef struct {int a;} result;

result* do_computation() {return nullptr;}

#if LOCKS_JSON
{"no_timing": {"spin_states": {"S1": 4, "S2": 0}}}
#endif //LOCKS_JSON

// CPU 0
DeclareTask(T1);
DeclareTask(T3); // autostart
// CPU 1
DeclareTask(T2);
DeclareTask(T4);

DeclareSpinlock(S1);
DeclareSpinlock(S2);

TEST_MAKE_OS_MAIN( StartOS(0) )

TASK(T3) {
	GetSpinlock(S1);
	/* ... */
	ActivateTask(T4);
	ActivateTask(T2);
	ActivateTask(T1);
	ReleaseSpinlock(S1);
	TerminateTask();
}

TASK(T1) {
	/* ... */
	TerminateTask();
}

TASK(T4) {
	result* result = do_computation();
	GetSpinlock(S1);
	/* ... */
	ReleaseSpinlock(S1);
	TerminateTask();
}

TASK(T2) {
	/* ... */
	TerminateTask();
}

