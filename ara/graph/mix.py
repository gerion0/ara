#define MIX 1 /*
# NOTE: This is a special file that can be read from Python and C++.
# It is used to define common enums between the Python model and C++ model.
import enum
class ABBType(enum.IntEnum): # */
    #undef pass
    #define pass namespace ara::graph { enum ABBType {
    pass

    not_implemented = 0,
    syscall = 0b1,
    call = 0b10,
    computation = 0b100,

    #undef pass
    #define pass };}
    pass


#undef MIX
#define MIX 1 /*
# lcf = local control flow
# icf = interprocedural control flow
# gcf = global control flow
# f2a = function to ABB
# a2f = ABB to function
class CFType(enum.IntEnum): # */
    #undef pass
    #define pass namespace ara::graph { enum CFType {
    pass

    lcf = 0,
    icf = 1,
    gcf = 2,
    f2a = 3,
    a2f = 4

    #undef pass
    #define pass };}
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
    #define pass namespace ara::graph { enum SyscallCategory {
    pass

    undefined = 0,
    every = 1,
    create = 2,
    comm = 3,

    #undef pass
    #define pass };}
    pass

#undef MIX
