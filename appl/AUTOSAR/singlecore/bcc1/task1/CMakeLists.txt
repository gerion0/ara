DOSEK_BINARY(
  NAME bcc1_task1a
  SYSTEM_DESC system.oil
  VERIFY verify_a.py
  LIBS libtest
  SOURCES
  a.cc
)

# This has to be done, since FSM is currently build with the APP-FSM
# method and not the CFG->GCFG method for SSE.
config_valid(VALID --systemcalls normal)
if(VALID)

DOSEK_BINARY(
  NAME bcc1_task1a_sse
  SYSTEM_DESC system.oil
  VERIFY verify_a.py
  LIBS libtest
  GENERATOR_ARGS -fgen-asserts -fsse
  SOURCES
  a.cc
  )
endif()

DOSEK_BINARY(
  NAME bcc1_task1b
  SYSTEM_DESC system.oil
  VERIFY verify_b.py
  LIBS libtest
  SOURCES
  b.cc
)

DOSEK_BINARY(
  NAME bcc1_task1c
  SYSTEM_DESC system.oil
  VERIFY verify_c.py
  LIBS libtest
  SOURCES
  c.cc
)

DOSEK_BINARY(
  NAME bcc1_task1d
  SYSTEM_DESC system.oil
  VERIFY verify_d.py
  LIBS libtest
  SOURCES
  d.cc
)

DOSEK_BINARY(
  NAME bcc1_task1e
  SYSTEM_DESC system.oil
  VERIFY verify_e.py
  LIBS libtest
  SOURCES
  e.cc
)

DOSEK_BINARY(
  NAME bcc1_task1f
  SYSTEM_DESC system.oil
  VERIFY verify_f.py
  LIBS libtest
  SOURCES
  f.cc
)

DOSEK_BINARY(
  NAME bcc1_task1g
  SYSTEM_DESC system.oil
  VERIFY verify_g.py
  LIBS libtest
  SOURCES
  g.cc 
)

