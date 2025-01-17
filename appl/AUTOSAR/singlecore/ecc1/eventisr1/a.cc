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


DeclareTask(H1);
DeclareTask(H2);
DeclareTask(H3);
DeclareEvent(E1, 1);

TEST_MAKE_OS_MAIN( StartOS(0) );

/* This test case waits for an event that was set in the alarm
   handler.
 */

TASK(H1) {
	test_trace('1');
	WaitEvent(E1);
	test_trace('}');

	/* The testcase has finished, check the output */
	test_trace_assert("1}");
	test_finish();
	ShutdownMachine();

	TerminateTask();
}

TASK(H2) {
	test_trace('-');
	TerminateTask();
}

TASK(H3) {
	TerminateTask();
}

ISR2(ISR1) {
	test_trace('!');
}

void PreIdleHook() {
}
