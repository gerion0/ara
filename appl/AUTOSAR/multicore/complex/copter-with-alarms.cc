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

//extern "C" volatile uint32_t random_source =0 ;
DeclareTask(SignalGatherInitiateTask);
DeclareTask(SignalGatherFinishedTask);
DeclareTask(SignalGatherTimeoutTask);
DeclareTask(SignalProcessingActuateTask);
DeclareTask(SignalProcessingAttitudeTask);
DeclareTask(FlightControlTask);
DeclareTask(FlightControlAttitudeTask);
DeclareTask(FlightControlActuateTask);
DeclareTask(MavlinkSendTask);
DeclareTask(CopterControlTask);
DeclareTask(MavlinkRecvHandler);

DeclareResource(SPIBus);
DeclareResource(SPIBus1);
DeclareSpinlock(SPIBusLock);

DeclareAlarm(CopterControlWatchdogAlarm);

TEST_MAKE_OS_MAIN( StartOS(0) )

int round;

TASK(SignalGatherInitiateTask) {
	if (round == 9) {
		test_trace(0x00);
		test_finish();
		ShutdownMachine();
	}
	test_trace(0x01);
	GetResource(SPIBus);
	GetSpinlock(SPIBusLock);
	test_trace(0x02);
	if ((round % 2) == 0) {
		ActivateTask(SignalGatherTimeoutTask);
		test_trace(0x03);
	} else {
		ActivateTask(SignalGatherFinishedTask);
		test_trace(0x04);
	}
	round ++;
	test_trace(0x05);
	ReleaseSpinlock(SPIBusLock);
	ReleaseResource(SPIBus);
	test_trace(0x06);
	TerminateTask();
}

TASK(SignalGatherFinishedTask) {
	test_trace(0x11);
	ActivateTask(SignalProcessingAttitudeTask);
	test_trace(0x12);
	ActivateTask(SignalProcessingActuateTask);
	test_trace(0x13);
	TerminateTask();
}

TASK(SignalGatherTimeoutTask) {
	test_trace(0x21);
	GetResource(SPIBus);
	GetSpinlock(SPIBusLock);
	test_trace(0x22);
	ReleaseSpinlock(SPIBusLock);
	ReleaseResource(SPIBus);
	test_trace(0x23);
	ChainTask(SignalGatherFinishedTask);
}

volatile int calculate;

TASK(SignalProcessingActuateTask) {
	test_trace(0x31);
	//for (calculate = 0; calculate < 200; calculate++);
	test_trace(0x30 | (calculate & 0xf));
	TerminateTask();
}

TASK(SignalProcessingAttitudeTask) {
	test_trace(0x41);
	//for (calculate = 0; calculate < 200; calculate++);
	test_trace(0x40 | (calculate & 0xf));
	TerminateTask();
}

TASK(FlightControlTask) {
	test_trace(0x51);
	ActivateTask(FlightControlAttitudeTask);
	test_trace(0x52);
	ActivateTask(FlightControlActuateTask);
	test_trace(0x53);
	ActivateTask(MavlinkSendTask);
	test_trace(0x54);
	TerminateTask();
}

TASK(FlightControlAttitudeTask) {
	test_trace(0x61);
	TerminateTask();
}

TASK(FlightControlActuateTask) {
	test_trace(0x71);
	TerminateTask();
}

TASK(MavlinkSendTask) {
	test_trace(0x81);
	GetResource(SPIBus1);
	GetSpinlock(SPIBusLock);
	test_trace(0x82);
	// Machine::trigger_interrupt_from_user(37);
	ReleaseSpinlock(SPIBusLock);
	ReleaseResource(SPIBus1);
	test_trace(0x83);
	TerminateTask();
}

TASK(CopterControlTask) {
	test_trace(0x91);
	SuspendAllInterrupts();
	test_trace(0x92);
	ResumeAllInterrupts();
	test_trace(0x93);
	if (round < 5) {
		CancelAlarm(CopterControlWatchdogAlarm);
		test_trace(0x94);
		SetRelAlarm(CopterControlWatchdogAlarm, 110, 100);
	}
	test_trace(0x95);

	TerminateTask();
}

ISR2(MavLinkRecvHandler) {
#ifndef CONFIG_ARCH_OSEK_V
	test_trace(0xA1);
#endif

	ActivateTask(CopterControlTask);
#ifndef CONFIG_ARCH_OSEK_V
	test_trace(0xA2);
#endif
}

TASK(CopterControlWatchdogTask) {
	test_trace(0xB1);
	TerminateTask();
}


void PreIdleHook() {
	kout << "I" << round << endl;
}
