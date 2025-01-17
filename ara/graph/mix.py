#pragma once
#include <ostream>

#define EQUAL_OPERATOR(Name) bool operator==(const Name&, const int); bool operator==(const int, const Name&);
#define NOT_EQUAL_OPERATOR(Name) bool operator!=(const Name&, const int); bool operator!=(const int, const Name&);
#define STREAM_OPERATOR(Name) std::ostream& operator<<(std::ostream&, const Name&);
#define STANDARD_OPERATORS(Name) EQUAL_OPERATOR(Name) NOT_EQUAL_OPERATOR(Name) STREAM_OPERATOR(Name)
#define MIX 1 /*
# SPDX-FileCopyrightText: 2021 Bastian Fuhlenriede
# SPDX-FileCopyrightText: 2022 Jan Neugebauer
# SPDX-FileCopyrightText: 2023 Gerion Entrup <entrup@sra.uni-hannover.de>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# NOTE: This is a special file that can be read from Python and C++.
# It is used to define common enums between the Python model and C++ model.
import enum
class ABBType(enum.IntEnum): # */
    #undef pass
    #define pass namespace ara::graph { enum class ABBType {
    pass

    not_implemented = 0,
    syscall = 0b1,
    call = 0b10,
    computation = 0b100,

    #undef pass
    #define pass }; STANDARD_OPERATORS(ABBType)}
    pass


#undef MIX
#define MIX 1 /*
import enum
class NodeLevel(enum.IntEnum): # */
    #undef pass
    #define pass namespace ara::graph { enum class NodeLevel {
    pass

    function = 0b1,
    abb = 0b10,
    bb = 0b100,

    #undef pass
    #define pass }; STANDARD_OPERATORS(NodeLevel)}
    pass


#undef MIX
#define MIX 1 /*
# lcf = local control flow
# icf = interprocedural control flow
# gcf = global control flow
# f2a = function to ABB
# a2b = ABB to BB
class CFType(enum.IntEnum): # */
    #undef pass
    #define pass namespace ara::graph { enum class CFType {
    pass

    lcf = 1 << 0,
    icf = 1 << 1,
    gcf = 1 << 2,
    f2a = 1 << 3,
    a2b = 1 << 4,
    f2b = 1 << 5

    #undef pass
    #define pass }; STANDARD_OPERATORS(CFType)}
    pass

#undef MIX
#define MIX 1 /*
# undefined = as the name says
# every = syscall belongs to every category
# create = syscall creates an instance
# comm = syscall is causes some kind of communication
# ATTENTION: This enum must kept in sync with syscall_category.inc
class SyscallCategory(enum.IntEnum): # */
    #undef pass
    #define pass namespace ara::graph { enum class SyscallCategory {
    pass

    undefined = 0,
    every  = 0b11,
    create = 0b10,
    comm   = 0b01,

    #undef pass
    #define pass }; STANDARD_OPERATORS(SyscallCategory)}
    pass

#undef MIX
#define MIX 1 /*
# Signature Type, whether the syscall argument is expected to be a value or
# symbol
#
# undefined = as the name says
# value = syscall argument is a value (42, "hello world", nullptr, ...)
# symbol = syscall argument is a symbol (Function, GlobalPointer, nullptr, ...)
# instance = syscall argument is an instance handler
# ATTENTION: This enum must kept in sync with syscall_category.inc
class SigType(enum.IntEnum): # */
    #undef pass
    #define pass namespace ara::graph { enum class SigType {
    pass

    undefined = 0,
    value = 1,
    symbol = 2,
    instance = 3,

    #undef pass
    #define pass }; STANDARD_OPERATORS(SigType)}
    pass

#undef MIX
#define MIX 1 /*
# StateType: describe the node type within the MSTG
#
# state = The node represents a single core system state
# metastate = The node links to a set of system states.
# entry_sync = The node describes a synchronisation point entry.
# exit_sync = The node describes a synchronisation point exit.
class StateType(enum.IntEnum): # */
    #undef pass
    #define pass namespace ara::graph { enum class StateType {
    pass

    state = 1,
    metastate = 2,
    entry_sync = 4,
    exit_sync = 8,

    #undef pass
    #define pass }; STANDARD_OPERATORS(StateType)}
    pass

#undef MIX
#define MIX 1 /*
# MSTType: Multi state transition type
#
# m2s = metastate to state
# st2sy = state to sync (or vice versa)
# s2s = state to state (normal SSE transition)
# sy2sy = sync to sync (parent to child, where the parent has greater context)
# follow_sync = sync to sync (which follows in the time domain)
# en2ex = edge between an entry and exit sync state
# m2sy = edge between a metastate and a sync state
# sync_neighbor = mark two sync states that has an equal outcome
class MSTType(enum.IntEnum): # */
    #undef pass
    #define pass namespace ara::graph { enum class MSTType {
    pass

    m2s = 1 << 0,
    st2sy = 1 << 1,
    s2s = 1 << 2,
    sy2sy = 1 << 3,
    follow_sync = 1 << 4,
    en2ex = 1 << 5,
    m2sy = 1 << 6,
    sync_neighbor = 1 << 7,

    #undef pass
    #define pass }; STANDARD_OPERATORS(MSTType)}
    pass

#undef MIX
#define MIX 1 /*
class GraphType(enum.IntEnum): # */
    #undef pass
    #define pass namespace ara::graph { enum class GraphType {
    pass

    ABB = 0,
    INSTANCE = 1,
    CALLGRAPH = 2,
    SVFG = 3,

    #undef pass
    #define pass }; STANDARD_OPERATORS(GraphType)}
    pass

#undef EQUAL_OPERATOR
#undef NOT_EQUAL_OPERATOR
#undef STREAM_OPERATOR
#undef STANDARD_OPERATORS


#undef pass
#define pass namespace ara::constants { constexpr const char*
pass

ARA_ENTRY_POINT = "__ara_fake_entry"

#undef pass
#define pass ;}
pass

#undef pass
