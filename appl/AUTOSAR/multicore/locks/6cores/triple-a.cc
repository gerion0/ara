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
{"no_timing": {"spin_states": {"S1": 0, "S2": 0, "S3": 0}}}
#endif //LOCKS_JSON





DeclareTask(T01);
DeclareTask(T11);
DeclareTask(T21);
DeclareTask(T31);
DeclareTask(T41);
DeclareTask(T51);
DeclareTask(T02);
DeclareTask(T12);
DeclareTask(T22);
DeclareTask(T32);
DeclareTask(T42);
DeclareTask(T52);
DeclareTask(T03);
DeclareTask(T13);
DeclareTask(T23);
DeclareTask(T33);
DeclareTask(T43);
DeclareTask(T53);
DeclareSpinlock(S1);
DeclareSpinlock(S2);
DeclareSpinlock(S3);

TEST_MAKE_OS_MAIN( StartOS(0) )

TASK(T01) {
	GetSpinlock(S1);
	ReleaseSpinlock(S1);
	ActivateTask(T11);
	TerminateTask();
}

TASK(T11) {
	GetSpinlock(S1);
	ReleaseSpinlock(S1);
	ActivateTask(T21);
	TerminateTask();
}

TASK(T21) {
	GetSpinlock(S1);
	ReleaseSpinlock(S1);
	ActivateTask(T31);
	TerminateTask();
}

TASK(T31) {
	GetSpinlock(S1);
	ReleaseSpinlock(S1);
	ActivateTask(T41);
	TerminateTask();
}

TASK(T41) {
	GetSpinlock(S1);
	ReleaseSpinlock(S1);
	ActivateTask(T51);
	TerminateTask();
}

TASK(T51) {
	GetSpinlock(S1);
	ReleaseSpinlock(S1);
	ActivateTask(T01);
	TerminateTask();
}


TASK(T02) {TerminateTask();}
TASK(T12) {TerminateTask();}
TASK(T22) {TerminateTask();}
TASK(T32) {TerminateTask();}
TASK(T42) {TerminateTask();}
TASK(T52) {TerminateTask();}

TASK(T03) {TerminateTask();}
TASK(T13) {TerminateTask();}
TASK(T23) {TerminateTask();}
TASK(T33) {TerminateTask();}
TASK(T43) {TerminateTask();}
TASK(T53) {TerminateTask();}
