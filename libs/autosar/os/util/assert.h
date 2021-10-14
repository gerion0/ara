#ifndef __ASSERT_H__
#define __ASSERT_H__

/**
 * @file
 * @ingroup os
 * @brief Static and runtime asserts
 */

#include "../../arch/posix/machine.h"

#ifdef assert
#undef assert
#endif

// declared in helper.cc
extern "C" uint32_t color_assert_port;
#define COLOR_ASSERT_UNKOWN 0xb83829de
#define COLOR_ASSERT_CFG_REGION 0xf4d9f7ca
#define COLOR_ASSERT_SYSTEM_STATE 0x9451210d

//! Runtime assert, print assertion if debugging, else causes trap
#ifndef NDEBUG
#include "../../arch/posix/output.h"
#define assert(x)                                                                                                      \
	{                                                                                                                  \
		if ((x) == 0) {                                                                                                \
			kout << "ASSERT " << __FILE__ << ":" << __LINE__ << " " << __func__ << ":\n  " << #x << endl;              \
			Machine::halt();                                                                                           \
		}                                                                                                              \
	}

#define color_assert(x, color)                                                                                         \
	{                                                                                                                  \
		if ((x) == 0) {                                                                                                \
			kout << "ASSERT " << __FILE__ << ":" << __LINE__ << " " << __func__ << endl;                               \
			color_assert_port = color;                                                                                 \
			Machine::halt();                                                                                           \
		}                                                                                                              \
	}

#else
#define assert(x)                                                                                                      \
	do {                                                                                                               \
		if ((x) == 0)                                                                                                  \
			Machine::debug_trap();                                                                                     \
	} while (0)
#define color_assert(x, color)                                                                                         \
	do {                                                                                                               \
		if ((x) == 0) {                                                                                                \
			color_assert_port = (color);                                                                               \
			Machine::debug_trap();                                                                                     \
		}                                                                                                              \
	} while (0)

#endif

#ifdef FAIL
#undef assert
#define assert(x) color_assert(x, COLOR_ASSERT_UNKOWN)
#endif

#define assume(expr) ((expr) ? static_cast<void>(0) : __builtin_unreachable())

//! Compile-time assert for constants as optimized by the compiler
#define pseudo_static_assert(A, T)                                                                                     \
	{                                                                                                                  \
		if (!(A)) {                                                                                                    \
			asm volatile("assertion failed: " T);                                                                      \
		}                                                                                                              \
	}

#endif /* __ASSERT_H__ */
