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



DeclareTask(T01);
DeclareTask(T11);
DeclareTask(T21);
DeclareSpinlock(S1);
DeclareSpinlock(S2);
DeclareSpinlock(S3);

TEST_MAKE_OS_MAIN( StartOS(0) )

TASK(T01) {
	GetSpinlock(S3);
	TerminateTask();
}

TASK(T11) {
	ActivateTask(T01);
	GetSpinlock(S1);
	ReleaseSpinlock(S1);
	GetSpinlock(S2);
	ReleaseSpinlock(S2);
}


TASK(T21) {
	TerminateTask();
}
