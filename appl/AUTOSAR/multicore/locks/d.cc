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


// Test memory protection (spanning over more than one 4k page in x86)
//volatile int testme[1024*4*10] __attribute__ ((section (".data.Handler12")));

DeclareTask(T01);
DeclareTask(T11);
DeclareSpinlock(S1);
DeclareSpinlock(S2);

TEST_MAKE_OS_MAIN( StartOS(0) )

TASK(T01) {
	ActivateTask(T11);
	while(true) {
		GetSpinlock(S1);
		ReleaseSpinlock(S1);
	}
	TerminateTask();
}

TASK(T11) {
	while(true) {
		GetSpinlock(S1);
		ReleaseSpinlock(S1);
	}
}
