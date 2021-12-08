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

DeclareTask(Handler11);
DeclareTask(Handler12);
DeclareTask(Handler13);

TEST_MAKE_OS_MAIN( StartOS(0) )

TASK(Handler11) {
#if !defined(CONFIG_ARCH_PATMOS)
    volatile int i = 1;
    while (i <  200000) i++;
#endif

    test_trace('a');
    ActivateTask(Handler12);


#if !defined(CONFIG_ARCH_PATMOS)
    i = 0;
    while (i <  200000) i++;
#endif
    test_trace('b');
    ActivateTask(Handler13);
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
	kout << "idle" << endl;
	/* The testcase has finished, check the output */
	test_trace_assert("ab3c2");
	test_finish();
	ShutdownMachine();
}
