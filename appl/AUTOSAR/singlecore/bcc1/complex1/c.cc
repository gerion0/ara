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
#include "syscall.h"


DeclareTask(H1);
DeclareTask(H2);
DeclareTask(H3);


TEST_MAKE_OS_MAIN(StartOS(0))

static int cycle_count;


TASK(H1) {
	test_trace('1');
	TerminateTask();
}

TASK(H2) {
	test_trace('2');
	Machine::trigger_interrupt_from_user(5);
	test_trace('_');
	TerminateTask();
}

TASK(H3) {
	test_trace('3');
	ChainTask(H1);
}

ISR2(ISR1) {
	test_trace('{');
	ActivateTask(H3);
	test_trace('}');
}

void PreIdleHook() {
	/* The testcase has finished, check the output */
	cycle_count++;

	if (cycle_count > 3) {
		test_trace_assert("2{}_312{}_312{}_31");
		test_finish();
		ShutdownMachine();
	}
}

