/**
 * @defgroup apps Applications
 * @brief The applications...
 */

/**
 * @file
 * @ingroup apps
 * @brief Just a simple test application
 */
#include "os.h"
#include "test/test.h"


DeclareTask(Handler11);
DeclareTask(Handler12);
DeclareTask(Handler13);

TEST_MAKE_OS_MAIN(
	StartOS(0);
				  )

TASK(Handler11) {
	test_trace('a');
	ActivateTask(Handler13);
	test_trace('b');
	ActivateTask(Handler12);
	test_trace('c');
	TerminateTask();
}

TASK(Handler12) {
	test_trace('2');
	TerminateTask();
}

TASK(Handler13) {
	test_trace('3');
	TerminateTask();
}

void PreIdleHook() {
	/* The testcase has finished, check the output */
	test_trace_assert("abc32");
	test_finish();
	ShutdownMachine();
}
