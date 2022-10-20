#ifndef __INLINE_H__
#define __INLINE_H__

/**
 * @file
 * @ingroup os
 * @brief Inline macros
 */

#ifdef __cplusplus__
#define __cpluplus
#endif

#ifdef __cplusplus
#define EXTERN_C_DECL extern "C"
#else
#define EXTERN_C_DECL
#endif

#define noinline __attribute__((noinline))
#define forceinline inlinehint inline
#define inlinehint __attribute__((always_inline))

#endif /* __INLINE_H__ */
