import pyllco
from dataclasses import dataclass
from typing import Any
from ara.graph import SyscallCategory, SigType

from ..os_util import syscall, Arg
from .posix_utils import IDInstance, logger, register_instance, add_edge_from_self_to, CurrentSyscallCategories, PosixOptions

@dataclass
class Mutex(IDInstance):
    wanted_attrs = ["name", "num_id"]
    dot_appearance = {
        "shape": "box",
        "fillcolor": "#2980b9",
        "style": "filled"
    }

    def __post_init__(self):
        super().__init__()

class MutexSyscalls:

    # int pthread_mutex_init(pthread_mutex_t *restrict mutex,
    #   const pthread_mutexattr_t *restrict attr);
    @syscall(aliases={"__pthread_mutex_init"},
             categories={SyscallCategory.create},
             signature=(Arg('mutex', hint=SigType.instance),
                        Arg('attr', hint=SigType.symbol)))
    def pthread_mutex_init(graph, abb, state, args, va):
        new_mutex = Mutex(name=None)
        args.mutex = new_mutex
        return register_instance(new_mutex, f"{new_mutex.name}", graph, abb, state)


    def mutex_interaction_impl(graph, abb, state, args, va, edge_label: str):
        """The Implementation of all Mutex Interaction Calls"""

        # If Category "create": Create a new Mutex object if args.mutex is a pyllco.GlobalVariable (args.mutex = PTHREAD_MUTEX_INITIALIZER)
        if SyscallCategory.create in CurrentSyscallCategories.get():
            if PosixOptions.enable_static_init_detection and type(args.mutex) == pyllco.GlobalVariable:
                new_mutex = Mutex(name=None)
                args.mutex = new_mutex
                state = register_instance(new_mutex, f"{new_mutex.name}", graph, abb, state)

        # If Category "comm": Handle the edge creation in a normal way.
        if SyscallCategory.comm in CurrentSyscallCategories.get():
            if type(args.mutex) != pyllco.GlobalVariable or not PosixOptions.enable_static_init_detection:
                state = add_edge_from_self_to(state, args.mutex, edge_label)
            else:
                logger.warning("Could not create Mutex interaction edge. args.mutex is of type pyllco.GlobalVariable. Probably there was an error in the PTHREAD_MUTEX_INITIALIZER detection.")

        return state

    # int pthread_mutex_lock(pthread_mutex_t *mutex);
    @syscall(aliases={"__pthread_mutex_lock"},
             categories={SyscallCategory.create, SyscallCategory.comm},
             signature=(Arg('mutex', hint=SigType.instance, ty=[Mutex, pyllco.GlobalVariable]),))
    def pthread_mutex_lock(graph, abb, state, args, va):
        return MutexSyscalls.mutex_interaction_impl(graph, abb, state, args, va, "pthread_mutex_lock()")

    # int pthread_mutex_unlock(pthread_mutex_t *mutex);
    @syscall(aliases={"__pthread_mutex_unlock"},
             categories={SyscallCategory.create, SyscallCategory.comm},
             signature=(Arg('mutex', hint=SigType.instance, ty=[Mutex, pyllco.GlobalVariable]),))
    def pthread_mutex_unlock(graph, abb, state, args, va):
        return MutexSyscalls.mutex_interaction_impl(graph, abb, state, args, va, "pthread_mutex_unlock()")