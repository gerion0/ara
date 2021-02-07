from .os_util import syscall, get_argument
from .os_base import OSBase
from ara.util import get_logger
from ara.graph import SyscallCategory, SigType
from dataclasses import dataclass
import ara.graph as _graph
import pyllco
import html
import graph_tool
import re

logger = get_logger("ZEPHYR")

class ZephyrInstance:
    def attribs_to_dot(self, attribs: [str]):
        return "<br/>".join([f"<i>{a}</i>: {html.escape(str(getattr(self, a)))}" for a in attribs])

    def instance_dot(self, attribs: [str], color: str):
        return {
            "shape": "box",
            "fillcolor": color,
            "style": "filled",
            "sublabel": self.attribs_to_dot(attribs)
        }

    # TODO: This is a work around until there is a general abstraction for runnable instances
    def has_entry(self):
        return hasattr(self, "entry_abb")

# The node representing the Zehpyr kernel. This should only exist once in the instance graph.
# It it used for syscalls that do not operate on user created instances but rather on ones
# that are build into the kernel e.g. the scheduler or the system heap.
@dataclass
class ZephyrKernel(ZephyrInstance):
    # Size of the system heap. Zero if not present
    heap_size: int
    # Always none, but required
    data: object = None
    def as_dot(self):
        attribs = ["heap_size"]
        return self.instance_dot(attribs, "#6fbf87")

# SSE finds suitable entrypoints by using isinstance (_iterate_tasks(). This reuquries hashability).
# There are two way this can be achieved with dataclasses. Either mark them as frozen
# (== immutable) or use unsafe_hash to generate a hash that might break if fields change.
#@dataclass(unsafe_hash=True)
@dataclass(frozen=True)
class Thread(ZephyrInstance):
    # Pointer to uninitialized struct k_thread.
    data: object
    # Pointer to the stack space.
    stack: object
    # Stack size in bytes.
    stack_size: int
    # Thread entry function.
    entry: object
    # Name of the entry function
    entry_name: str
    # The first abb of the entry function. Used to ensure the required 
    # compatability with the freertos.Tasks. SSE depends on it.
    entry_abb: object
    # 3 parameters that are passed to the entry function.
    # NOTE This has to be a tuple, lists are not hashable
    entry_params: (object, object, object)
    # Thread priority.
    priority: int
    # Thread options.
    options: int
    # Scheduling delay, or K_NO_WAIT (for no delay).
    delay: int

    def as_dot(self):
        attribs = ["entry_name", "stack_size", "priority", "options", "delay"]
        return self.instance_dot(attribs, "#6fbf87")

# Interrupt service routine. Like every other kernel resource, these can be created
# dynamically via irq_connect_dynamic() (which is not a syscall) or statically by 
# using the IRQ_CONNECT macro. The latter might be harder to detect since the actual 
# implementation is arch dependend.
# Most of the embedded architectures like riscv and arm seem to use Z_ISR_DECLARE()
# internally.
@dataclass(frozen=True)
class ISR(ZephyrInstance):
    # The irq line number
    irq_number: int
    # The priority. Might be ignored if the architecture's interrupt controller does not support
    # that
    priority: int
    # The handler function
    entry: object
    # The name of the hander function
    entry_name: str
    # The first abb of the handler function. Needed for SSE (see Thread.entry_abb)
    entry_abb: object
    # Parameter for the handler
    handler_param: object
    # Architecture specific flags
    flags: int
    # Always none but required for all zephyr instances
    data: object = None

    def as_dot(self):
        attribs = ["irq_number", "priority", "entry_name", "flags"]
        return self.instance_dot(attribs, "#6fbf87")

# There are actually two types of semaphores: k_sems are kernelobjects that are
# managed via the k_sem_* syscalls while sys_sems live in user memory (provided
# user mode is enabled). Right now, only k_sems can be detected.
@dataclass
class Semaphore(ZephyrInstance):
    # Pointer to unitialized struct k_sem
    data: object
    # The internal counter
    count: int
    # The maximum permitted count
    limit: int

    def as_dot(self):
        attribs = ["count", "limit"]
        return self.instance_dot(attribs, "#6fbf87")

@dataclass
class KernelSemaphore(Semaphore):
    pass

@dataclass
class UserSemaphore(Semaphore):
    pass

@dataclass
class Mutex(ZephyrInstance):
    #The k_mutex object
    data: object

    def as_dot(self):
        attribs = []
        return self.instance_dot(attribs, "#6fbf87")

# The zephyr kernel offers two kinds of queues: FIFO and LIFO which both use queues internally
# They are created via separate "functions" k_{lifo,fifo}_init
# Both of those are just macros wrapping the actual k_queue_init syscall which makes them
# hard to detect. For now, we do not diffrentiate between types of queues.
# On a positive note, since these are macros no action is needed to make ARA detect the
# underlying k_queue_init sycalls. Were they functions, they might not be contained in libapp
# TODO: Think about detection of lifo and fifo queues.
@dataclass
class Queue(ZephyrInstance):
    # The k_queue object
    data: object

    def as_dot(self):
        attribs = []
        return self.instance_dot(attribs, "#6fbf87")

# Stacks are created via the k_stack_alloc_init syscall which allocates an internal buffer.
# However, it is also possible to initialize a stack with a given buffer with k_stack_init 
# which is NOT a syscall.
# TODO: Find out if k_stack_init should be detected as well.
@dataclass
class Stack(ZephyrInstance):
    # The k_stack object
    data: object
    # The buffer where elements are stacked
    buf: object
    # The max number of entries that this stack can hold
    max_entries: int

    def as_dot(self):
        attribs = ["max_entries"]
        return self.instance_dot(attribs, "#6fbf87")

# Pipes can be created with two syscalls, k_pipe_init requries a user allocted buffer, 
# while k_pipe_alloc_init creates one from the internal memory pool.
@dataclass
class Pipe(ZephyrInstance):
    # The k_pipe object
    data: object
    # The size of the backing ring buffer in bytes
    size: int
    def as_dot(self):
        attribs = ["size"]
        return self.instance_dot(attribs, "#6fbf87")

# Heaps are created by the user as neccessary and can be shared between threads.
# However, using k_malloc and k_free, threads also have access to a system memory pool.
@dataclass
class Heap(ZephyrInstance):
    # The k_heap object, None for the system memory pool since it cannot be referecend by app code.
    data: object
    # The max size
    limit: int

    def as_dot(self):
        attribs = ["limit"]
        return self.instance_dot(attribs, "#6fbf87")

@dataclass
class MSGQ(ZephyrInstance):
    # The k_msgq object
    data: object
    # The size of a single message
    msg_size: int
    # This max number of messages that fit into the buffer
    max_msgs: int
    def as_dot(self):
        attribs = ["msg_size", "max_msgs"]
        return self.instance_dot(attribs, "#6fbf87")

@dataclass
class Empty(ZephyrInstance):
    def as_dot(self):
        attribs = []
        return self.instance_dot(attribs, "#6fbf87")

llvm_suffix = re.compile(".+\.\d+")

class ZEPHYR(OSBase):
    vertex_properties = [('label', 'string', 'instance name'),
                         ('obj', 'object', 'instance object (e.g. Task)'),
                         ]
    edge_properties = [('label', 'string', 'syscall name')]

    """The kernel node"""
    kernel = None

    """A dict<str, int> that stores the number of times an identifier was requested."""
    id_count = {}

    """A dict<abb(Vertex), instance(Vertex)> tracking which entry point was explored with which
    running instance."""
    explored_entry_points = {}

    @staticmethod
    def get_special_steps():
        return ["ZephyrStaticPost"]

    @staticmethod
    def has_dynamic_instances():
        return True

    @staticmethod
    def drop_llvm_suffix(name):
        if llvm_suffix.match(name) is not None:
            return name.rsplit('.', 1)[0]
        return name

    @classmethod
    def is_syscall(cls, function_name):
        # Drop the llvm suffix for all functions. Should not pose a problem since they can't occur
        # in regular C identifiers
        alias_name = function_name
        function_name = ZEPHYR.drop_llvm_suffix(function_name)

        if hasattr(cls, function_name) and hasattr(getattr(cls, function_name), 'syscall'):
            if alias_name != function_name:
                getattr(cls, function_name).aliases.append(alias_name)
            return True
        return False

    @staticmethod
    def add_normal_cfg(cfg, abb, state):
        for oedge in cfg.vertex(abb).out_edges():
            if cfg.ep.type[oedge] == _graph.CFType.lcf:
                state.next_abbs.append(oedge.target())

    @staticmethod
    def get_unique_id(ident: str) -> str:
        """Generate a unique id by taking the actual one and appending a number to deduplicate"""
        count = ZEPHYR.id_count.get(ident)
        if count is None:
            ZEPHYR.id_count[ident] = 1
        else:
            ZEPHYR.id_count[ident] = count + 1
            ident = f"{ident}.{count}"

        return ident

    @staticmethod
    def create_instance(cfg, abb, state, label: str, obj: ZephyrInstance, ident: str, call: str):
        """
        Adds a new instance and an edge for the create syscall to the instance graph.
        If there already exists an instance that is matched to the same symbol another one will be
        created and will inherit all interactions from his sibling. All future comm syscalls will
        add edges to all instances that share the same symbol. There is currently no way to
        distinguish between them. Those rules also apply to instances that add entry points (Thread, ISR).
        An exception is made for instances that share entry points. Adding one of those will mark
        add new info to the instance graph."""
        if obj.has_entry():
            # For now assume that no entry points are shared between different instance types
            original = ZEPHYR.explored_entry_points.get(obj.entry_abb)
            if original != None:
                # When we encounter a thread creation with an already searched entry point, mark all
                # instances as non unique
                logger.warning(f"Creation of instance with already known entry point, marking as non unique. {obj}")
                clones = [original]
                # Mark the clone and all his created instances as non unique.
                while len(clones) > 0:
                    clone = clones.pop(0)
                    state.instances.vp.unique[clone] = False
                    for e, n in zip(clone.out_edges(), clone.out_neighbors()):
                        syscall = getattr(ZEPHYR, state.instances.ep.label[e])
                        if ZEPHYR.syscall_in_category(syscall, SyscallCategory.create):
                            state.instances.vp.unique[n] = False
                            # If we find an instance which is now non-unique and adds an entry point we
                            # need to repeat the process for its node.
                            if clone.has_entry():
                                clones.append(n)

                return

        siblings = list(ZEPHYR.find_instance_by_symbol(state, obj.data))

        instances = state.instances
        v = instances.add_vertex()
        instances.vp.label[v] = label
        instances.vp.obj[v] = obj
        instances.vp.id[v] = ZEPHYR.get_unique_id(ident)
        instances.vp.branch[v] = state.branch
        instances.vp.loop[v] = state.loop
        instances.vp.after_scheduler[v] = state.scheduler_on
        # Creating an instance from a thread that is not unique will result in a non unique instance
        instances.vp.unique[v] = not (state.branch or state.loop) and instances.vp.unique[state.running]
        instances.vp.soc[v] = abb
        instances.vp.llvm_soc[v] = cfg.vp.entry_bb[abb]
        instances.vp.file[v] = cfg.vp.file[abb]
        instances.vp.line[v] = cfg.vp.line[abb]
        instances.vp.specialization_level[v] = ""

        if obj.has_entry():
            ZEPHYR.explored_entry_points[obj.entry_abb] = v

        # If we have some siblings, clone all edges
        to_add = []
        if len(siblings) > 0:
            logger.warning(f"Multiple init calls to same symbol: {obj.data}")
            for c in siblings[0].out_edges():
                to_add.append(((v, c.target()), instances.ep.label[c]))
            for c in siblings[0].in_edges():
                # Ignore the syscall that created the siblings
                syscall = getattr(ZEPHYR, state.instances.ep.label[c])
                if not ZEPHYR.syscall_in_category(syscall, SyscallCategory.create):
                    to_add.append(((c.source(), v), instances.ep.label[c]))
            for ((s, t), label) in to_add:
                e = instances.add_edge(s, t)
                instances.ep.label[e] = label
        ZEPHYR.add_comm(state, v, call)

    @staticmethod
    def find_instance_by_symbol(state, instance):
        if instance is None:
            return []
        return filter(lambda v: state.instances.vp.obj[v].data == instance,
                state.instances.vertices())

    @staticmethod
    def add_comm(state, to, call: str):
            instance = state.running
            if instance == None:
                logger.error("syscall but no running instance. Maybe from main()?")
                return
            skip_duplicate_edges = True
            if skip_duplicate_edges:
                if len(list(filter(lambda e: e.target() == to and state.instances.ep.label[e] ==
                    call, instance.out_edges()))) > 0:
                        return
            e = state.instances.add_edge(instance, to)
            state.instances.ep.label[e] = call

    @staticmethod
    def add_instance_comm(state, instance, call: str):
        matches = list(ZEPHYR.find_instance_by_symbol(state, instance))
        if len(matches) == 0:
            logger.error(f"No matching instance found. Skipping.\n{type(instance)}\n{instance}")
        else:
            if len(matches) > 1:
                logger.warning(f"Multiple matching instances found.\n{[state.instances.vp.id[v] for v in matches][0]}")
            for match in matches:
                ZEPHYR.add_comm(state, match, call)

    @staticmethod
    def add_self_comm(state, call: str):
        ZEPHYR.add_comm(state, state.running, call)

    @staticmethod
    def init(state):
        pass

    @staticmethod
    def syscall_in_category(syscall, category):
        syscall_category = syscall.categories
        categories = set((category,))
        return SyscallCategory.every in categories or (syscall_category | categories) == syscall_category

    @staticmethod
    def interpret(cfg, abb, state, categories=SyscallCategory.every):
        syscall_name = cfg.get_syscall_name(abb)
        syscall_name = ZEPHYR.drop_llvm_suffix(syscall_name)

        syscall = getattr(ZEPHYR, syscall_name)

        if ZEPHYR.syscall_in_category(syscall, categories):
            logger.info(f"Interpreting syscall: {syscall_name}")
            return syscall(cfg, abb, state)
        else:
            state = state.copy()
            state.next_abbs = []
            ZEPHYR.add_normal_cfg(cfg, abb, state)
            return state

    # k_tid_t k_thread_create(struct k_thread *new_thread, k_thread_stack_t *stack, size_t stack_size, 
    #   k_thread_entry_t entry, void *p1, void *p2, void *p3, int prio, uint32_t options,
    #   k_timeout_t delay)
    @syscall(categories={SyscallCategory.create},
             signature=(SigType.symbol, SigType.symbol, SigType.value,
                        SigType.symbol, SigType.value, SigType.value,
                        SigType.value, SigType.value, SigType.value,
                        SigType.value))
    def k_thread_create(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        stack = get_argument(cfg, abb, state.call_path, 1, ty=pyllco.Value)
        stack_size = get_argument(cfg, abb, state.call_path, 2)
        entry = get_argument(cfg, abb, state.call_path, 3, ty=pyllco.Function)
        entry_name = entry.get_name()
        entry_abb = cfg.get_entry_abb(cfg.get_function_by_name(entry_name))
        p1 = get_argument(cfg, abb, state.call_path, 4)
        p2 = get_argument(cfg, abb, state.call_path, 5)
        p3 = get_argument(cfg, abb, state.call_path, 6)
        entry_params = (p1, p2, p3)
        priority = get_argument(cfg, abb, state.call_path, 7)
        options = get_argument(cfg, abb, state.call_path, 8)
        delay = get_argument(cfg, abb, state.call_path, 9)

        instance = Thread(
            data,
            stack,
            stack_size,
            entry,
            entry_name,
            entry_abb,
            entry_params,
            priority,
            options,
            delay
        )

        ZEPHYR.create_instance(cfg, abb, state, "Thread", instance, data.get_name(), "k_thread_create")
        state.next_abbs = []

        ZEPHYR.add_normal_cfg(cfg, abb, state)
        return state

    # int irq_connect_dynamic(unsigned int irq, unsigned int priority, 
    #   void (*routine)(const void *parameter), const void *parameter, uint32_t flags)
    @syscall(categories={SyscallCategory.create},
             signature=(SigType.value, SigType.value, SigType.symbol,
                        SigType.value, SigType.value))
    def irq_connect_dynamic(cfg, abb, state):
        state = state.copy()

        irq_number = get_argument(cfg, abb, state.call_path, 0)
        priority = get_argument(cfg, abb, state.call_path, 1)
        entry = get_argument(cfg, abb, state.call_path, 2, ty=pyllco.Function)
        entry_name = entry.get_name()
        entry_abb = cfg.get_entry_abb(cfg.get_function_by_name(entry_name))
        handler_param = get_argument(cfg, abb, state.call_path, 3)
        flags = get_argument(cfg, abb, state.call_path, 4)

        instance = ISR(
            irq_number,
            priority,
            entry,
            entry_name,
            entry_abb,
            handler_param,
            flags
        )

        ZEPHYR.create_instance(cfg, abb, state, "ISR", instance, entry_name, "irq_connect_dynamic")

        state.next_abbs = []

        ZEPHYR.add_normal_cfg(cfg, abb, state)
        return state

    # int k_sem_init(struct k_sem *sem, unsigned int initial_count, unsigned int limit)
    @syscall(categories={SyscallCategory.create},
            signature=(SigType.symbol, SigType.value, SigType.value))
    def k_sem_init(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        count = get_argument(cfg, abb, state.call_path, 1)
        limit = get_argument(cfg, abb, state.call_path, 2)

        instance = KernelSemaphore(
            data,
            count,
            limit
        )

        ZEPHYR.create_instance(cfg, abb, state, "KernelSemaphore", instance, data.get_name(), "k_sem_init")
        state.next_abbs = []

        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int sys_sem_init(struct sys_sem *sem, unsigned int initial_count, unsigned int limit)
    @syscall(categories={SyscallCategory.create},
            signature=(SigType.symbol, SigType.value, SigType.value))
    def sys_sem_init(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        count = get_argument(cfg, abb, state.call_path, 1)
        limit = get_argument(cfg, abb, state.call_path, 2)

        instance = UserSemaphore(
            data,
            count,
            limit
        )

        ZEPHYR.create_instance(cfg, abb, state, "UserSemaphore", instance, data.get_name(), "sys_sem_init")
        state.next_abbs = []

        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_mutex_init(struct k_mutex *mutex)
    @syscall(categories={SyscallCategory.create},
            signature=(SigType.symbol, ))
    def k_mutex_init(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        instance = Mutex(
            data
        )

        ZEPHYR.create_instance(cfg, abb, state, "Mutex", instance, data.get_name(), "k_mutex_init")
        state.next_abbs = []

        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_queue_init(struct k_queue *queue)
    # k_lifo_init(lifo)
    # k_fifo_init(fifo)
    @syscall(categories={SyscallCategory.create},
            signature=(SigType.symbol, ))
    def k_queue_init(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        instance = Queue(
            data
        )

        ZEPHYR.create_instance(cfg, abb, state, "Queue", instance, data.get_name(), "k_queue_init")
        state.next_abbs = []

        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_stack_init(struct k_stack *stack, stack_data_t *buffer, uint32_t num_entries)
    @syscall(categories={SyscallCategory.create},
            signature=(SigType.symbol, SigType.symbol, SigType.value))
    def k_stack_init(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        buf = get_argument(cfg, abb, state.call_path, 1, ty=pyllco.Value)
        max_entries = get_argument(cfg, abb, state.call_path, 2)

        instance = Stack(
            data,
            buf,
            max_entries
        )

        ZEPHYR.create_instance(cfg, abb, state, "Stack", instance, data.get_name(), "k_stack_init")
        state.next_abbs = []

        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_stack_init(struct k_stack *stack, stack_data_t *buffer, uint32_t num_entries)
    @syscall(categories={SyscallCategory.create},
            signature=(SigType.symbol, SigType.value))
    def k_stack_alloc_init(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        #buf = get_argument(cfg, abb, state.call_path, 1, ty=pyllco.Value)
        max_entries = get_argument(cfg, abb, state.call_path, 1)

        instance = Stack(
            data,
            # When creating a stack with k_stack_alloc_init() the buffer is created in kernel
            # address space
            None,
            max_entries
        )

        ZEPHYR.create_instance(cfg, abb, state, "Stack", instance, data.get_name(), "k_stack_alloc_init")
        state.next_abbs = []

        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

# void k_pipe_init(struct k_pipe *pipe, unsigned char *buffer, size_t size)
    @syscall(categories={SyscallCategory.create},
            signature=(SigType.symbol, SigType.symbol, SigType.value))
    def k_pipe_init(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        buf = get_argument(cfg, abb, state.call_path, 1, ty=pyllco.Value)
        size = get_argument(cfg, abb, state.call_path, 2)

        instance = Pipe(
            data,
            size
        )

        ZEPHYR.create_instance(cfg, abb, state, "Pipe", instance, data.get_name(), "k_pipe_init")
        state.next_abbs = []

        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_pipe_alloc_init(struct k_pipe *pipe, size_t size)
    @syscall(categories={SyscallCategory.create},
            signature=(SigType.symbol, SigType.value))
    def k_pipe_alloc_init(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        size = get_argument(cfg, abb, state.call_path, 1)

        instance = Pipe(
            data,
            size
        )

        ZEPHYR.create_instance(cfg, abb, state, "Pipe", instance, data.get_name(), "k_pipe_alloc_init")
        state.next_abbs = []

        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_heap_init(struct k_heap *h, void *mem, size_t bytes)
    @syscall(categories={SyscallCategory.create},
            signature=(SigType.symbol, SigType.symbol, SigType.value))
    def k_heap_init(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        #buf = get_argument(cfg, abb, state.call_path, 1, ty=pyllco.Value)
        limit = get_argument(cfg, abb, state.call_path, 2)

        instance = Heap(
            data,
            limit
        )

        ZEPHYR.create_instance(cfg, abb, state, "Heap", instance, data.get_name(), "k_heap_init")
        state.next_abbs = []

        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_msgq_init(struct k_msgq *q, char *buffer, size_t msg_size, uint32_t max_msgs)
    @syscall(categories={SyscallCategory.create},
            signature=(SigType.symbol, SigType.symbol, SigType.value, SigType.value))
    def k_msgq_init(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        #buf = get_argument(cfg, abb, state.call_path, 1, ty=pyllco.Value)
        msg_size = get_argument(cfg, abb, state.call_path, 2)
        max_msgs = get_argument(cfg, abb, state.call_path, 3)

        instance = MSGQ(
            data,
            msg_size,
            max_msgs
        )

        ZEPHYR.create_instance(cfg, abb, state, "MSGQ", instance, data.get_name(), "k_msgq_init")
        state.next_abbs = []

        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_msgq_alloc_init(struct k_msgq *msgq, size_t msg_size, uint32_t max_msgs)
    @syscall(categories={SyscallCategory.create},
            signature=(SigType.symbol, SigType.value, SigType.value))
    def k_msgq_alloc_init(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        msg_size = get_argument(cfg, abb, state.call_path, 1)
        max_msgs = get_argument(cfg, abb, state.call_path, 2)

        instance = MSGQ(
            data,
            msg_size,
            max_msgs
        )

        ZEPHYR.create_instance(cfg, abb, state, "MSGQ", instance, data.get_name(), "k_msgq_alloc_init")
        state.next_abbs = []

        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    #
    # Syscall.comm
    #

    #
    # Thread
    #

    # int k_thread_join(struct k_thread *thread, k_timeout_t timeout)
    @syscall(categories={SyscallCategory.comm},
            signature=(SigType.symbol, SigType.value))
    def k_thread_join(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        timeout = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_instance_comm(state, data, "k_thread_join")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int32_t k_sleep(k_timeout_t timeout)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.value,))
    def k_sleep(cfg, abb, state):
        state = state.copy()

        timeout = get_argument(cfg, abb, state.call_path, 0)

        ZEPHYR.add_self_comm(state, "k_sleep")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int32_t k_msleep(int32_t ms)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.value,))
    def k_msleep(cfg, abb, state):
        state = state.copy()

        ms = get_argument(cfg, abb, state.call_path, 0)

        ZEPHYR.add_self_comm(state, "k_msleep")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int32_t k_usleep(int32_t us)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.value,))
    def k_usleep(cfg, abb, state):
        state = state.copy()

        us = get_argument(cfg, abb, state.call_path, 0)

        ZEPHYR.add_self_comm(state, "k_usleep")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_busy_wait(uint32_t usec_to_wait)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.value,))
    def k_busy_wait(cfg, abb, state):
        state = state.copy()

        us = get_argument(cfg, abb, state.call_path, 0)

        ZEPHYR.add_self_comm(state, "k_busy_wait")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_yield(void)
    @syscall(categories={SyscallCategory.comm})
    def k_yield(cfg, abb, state):
        state = state.copy()

        ZEPHYR.add_self_comm(state, "k_yield")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_wakeup(k_tid_t thread)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.value, ))
    def k_wakeup(cfg, abb, state):
        state = state.copy()

        #ZEPHYR.add_self_comm(state, "k_wakeup")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # k_tid_t k_current_get(void)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.value, ))
    def k_current_get(cfg, abb, state):
        state = state.copy()

        tid = get_return_value(cfg, abb, state.call_path)
        print(tid)
        print(type(tid))

        ZEPHYR.add_self_comm(state, "k_current_get")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state


    # k_ticks_t k_thread_timeout_expires_ticks(struct k_thread *t)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_thread_timeout_expires_ticks(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_thread_timeout_expires_ticks")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # k_ticks_t k_thread_timeout_remaining_ticks(struct k_thread *t)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_thread_timeout_remaining_ticks(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_thread_timeout_remaining_ticks")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_sched_time_slice_set(int32_t slice, int prio)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.value, SigType.value))
    def k_sched_time_slice_set(cfg, abb, state):
        state = state.copy()

        time_slice = get_argument(cfg, abb, state.call_path, 0)
        prio = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_comm(state, ZEPHYR.kernel, "k_sched_time_slice_set")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_sched_lock(void)
    @syscall(categories={SyscallCategory.comm})
    def k_sched_lock(cfg, abb, state):
        state = state.copy()

        ZEPHYR.add_comm(state, ZEPHYR.kernel, "k_sched_lock")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_sched_unlock(void)
    @syscall(categories={SyscallCategory.comm})
    def k_sched_unlock(cfg, abb, state):
        state = state.copy()

        ZEPHYR.add_comm(state, ZEPHYR.kernel, "k_sched_unlock")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_thread_custom_data_set(void *value)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_thread_custom_data_set(cfg, abb, state):
        state = state.copy()

        custom_data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_self_comm(state, "k_thread_custom_data_set")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void *k_thread_custom_data_get(void)
    @syscall(categories={SyscallCategory.comm})
    def k_thread_custom_data_get(cfg, abb, state):
        state = state.copy()

        ZEPHYR.add_self_comm(state, "k_thread_custom_data_get")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    #
    # ISR
    #

    # bool k_is_in_isr(void)
    @syscall(categories={SyscallCategory.comm})
    def k_is_in_isr(cfg, abb, state):
        state = state.copy()

        ZEPHYR.add_self_comm(state, "k_is_in_isr")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_is_preempt_thread(void)
    @syscall(categories={SyscallCategory.comm})
    def k_is_preempt_thread(cfg, abb, state):
        state = state.copy()

        ZEPHYR.add_self_comm(state, "k_is_preempt_thread")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # bool k_is_pre_kernel(void)
    @syscall(categories={SyscallCategory.comm})
    def k_is_pre_kernel(cfg, abb, state):
        state = state.copy()

        ZEPHYR.add_self_comm(state, "k_is_pre_kernel")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    #
    # Semaphore
    #

    # int k_sem_take(struct k_sem *sem, k_timeout_t timeout)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value))
    def k_sem_take(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        timeout = get_argument(cfg, abb, state.call_path, 1)
        ZEPHYR.add_instance_comm(state, data, "k_sem_take")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_sem_give(struct k_sem *sem)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_sem_give(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_sem_give")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_sem_reset(struct k_sem *sem)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_sem_reset(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_sem_reset")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # unsigned int k_sem_count_get(struct k_sem *sem)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_sem_count_get(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_sem_count_get")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int sys_sem_take(struct sys_sem *sem, k_timeout_t timeout)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value))
    def sys_sem_take(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        timeout = get_argument(cfg, abb, state.call_path, 1)
        ZEPHYR.add_instance_comm(state, data, "sys_sem_take")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int sys_sem_give(struct sys_sem *sem)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def sys_sem_give(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "sys_sem_give")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # unsigned int sys_sem_count_get(struct sys_sem *sem)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def sys_sem_count_get(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "sys_sem_count_get")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    #
    # Mutex
    #

    # int k_mutex_lock(struct k_mutex *mutex, k_timeout_t timeout)
    # NOTE: The thread that has locked a mutex is eligible for priority inheritance.
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value))
    def k_mutex_lock(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        timeout = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_instance_comm(state, data, "k_mutex_lock")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_mutex_unlock(struct k_mutex *mutex)
    # Unlock should only ever be called by the locking thread.
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_mutex_unlock(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_mutex_unlock")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    #
    # Queue: FIFO and LIFO functions are just macro wrappers around the generic queue functions
    #

    # void k_queue_cancel_wait(struct k_queue *queue)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_queue_cancel_wait(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_queue_cancel_wait")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_queue_append(struct k_queue *queue, void *data)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value))
    def k_queue_append(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        item = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_instance_comm(state, data, "k_queue_append")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int32_t k_queue_alloc_append(struct k_queue *queue, void *data)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value))
    def k_queue_alloc_append(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        item = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_instance_comm(state, data, "k_queue_alloc_append")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_queue_prepend(struct k_queue *queue, void *data)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value))
    def k_queue_prepend(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        item = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_instance_comm(state, data, "k_queue_prepend")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_queue_alloc_prepend(struct k_queue *queue, void *data)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value))
    def k_queue_alloc_prepend(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        item = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_instance_comm(state, data, "k_queue_alloc_prepend")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_queue_insert(struct k_queue *queue, void *prev, void *data)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value, SigType.value))
    def k_queue_insert(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        prev = get_argument(cfg, abb, state.call_path, 1)
        item = get_argument(cfg, abb, state.call_path, 2)

        ZEPHYR.add_instance_comm(state, data, "k_queue_insert")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_queue_append_list(struct k_queue *queue, void *head, void *tail)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value, SigType.value))
    def k_queue_append_list(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        head = get_argument(cfg, abb, state.call_path, 1)
        tail = get_argument(cfg, abb, state.call_path, 2)

        ZEPHYR.add_instance_comm(state, data, "k_queue_append_list")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_queue_merge_slist(struct k_queue *queue, sys_slist_t *list)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.symbol))
    def k_queue_merge_slist(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        other = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_instance_comm(state, data, "k_queue_merge_list")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void *k_queue_get(struct k_queue *queue, k_timeout_t timeout)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value))
    def k_queue_get(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        into = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_instance_comm(state, data, "k_queue_get")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # bool k_queue_remove(struct k_queue *queue, void *data)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value))
    def k_queue_remove(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        other = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_instance_comm(state, data, "k_queue_remove")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # bool k_queue_unique_append(struct k_queue *queue, void *data)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value))
    def k_queue_unique_append(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        other = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_instance_comm(state, data, "k_queue_unique_append")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_queue_is_empty(struct k_queue *queue)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_queue_is_empty(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_queue_is_empty")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void *k_queue_peek_head(struct k_queue *queue)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_queue_peek_head(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_queue_peek_head")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void *k_queue_peek_tail(struct k_queue *queue)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_queue_peek_tail(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_queue_peek_tail")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    #
    # Stack
    #

    # int k_stack_cleanup(struct k_stack *stack)
    # NOTE: Should only be used if allocated with stack_alloc_init.
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_stack_cleanup(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_stack_cleanup")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_stack_push(struct k_stack *stack, stack_data_t data)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value))
    def k_stack_push(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        item = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_instance_comm(state, data, "k_stack_push")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_stack_pop(struct k_stack *stack, stack_data_t *data, k_timeout_t timeout)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value, SigType.value))
    def k_stack_pop(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        into = get_argument(cfg, abb, state.call_path, 1)
        timeout = get_argument(cfg, abb, state.call_path, 2)

        ZEPHYR.add_instance_comm(state, data, "k_stack_pop")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    #
    # Pipe
    #

    # int k_pipe_cleanup(struct k_pipe *pipe)
    # NOTE: Should only be used if allocated with pipe_alloc_init.
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_pipe_cleanup(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_pipe_cleanup")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_pipe_put(struct k_pipe *pipe, void *data, size_t bytes_to_write, size_t *bytes_written,
    # size_t min_xfer, k_timeout_t timeout)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.symbol, SigType.value, SigType.symbol, SigType.value,
                 SigType.value))
    def k_pipe_put(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        item = get_argument(cfg, abb, state.call_path, 1, ty=pyllco.Value)
        item_size = get_argument(cfg, abb, state.call_path, 2)
        # Does not really make sense as a value, since at call time this contains garbage
        #bytes_written = get_argument(cfg, abb, state.call_path, 3)
        min_bytes_to_write = get_argument(cfg, abb, state.call_path, 4)
        timeout = get_argument(cfg, abb, state.call_path, 5)

        ZEPHYR.add_instance_comm(state, data, "k_pipe_put")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_pipe_get(struct k_pipe *pipe, void *data, size_t bytes_to_read, size_t *bytes_read,
    # size_t min_xfer, k_timeout_t timeout)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.symbol, SigType.value, SigType.symbol, SigType.value,
                 SigType.value))
    def k_pipe_get(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        #item = get_argument(cfg, abb, state.call_path, 1)
        item_size = get_argument(cfg, abb, state.call_path, 2)
        # Does not really make sense as a value, since at call time this contains garbage
        #bytes_read = get_argument(cfg, abb, state.call_path, 3)
        min_bytes_to_read = get_argument(cfg, abb, state.call_path, 4)
        timeout = get_argument(cfg, abb, state.call_path, 5)

        ZEPHYR.add_instance_comm(state, data, "k_pipe_get")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_pipe_block_put(struct k_pipe *pipe, struct k_mem_block *block, size_t size, struct
    # k_sem *sem)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value, SigType.value, SigType.symbol))
    def k_pipe_block_put(cfg, abb, state):
        # This syscall actually works on more than one instance. It writes to a pipe and
        # calls give() on sem (which is OPTIONAL).
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        item = get_argument(cfg, abb, state.call_path, 1)
        item_size = get_argument(cfg, abb, state.call_path, 2)
        sem = get_argument(cfg, abb, state.call_path, 4)

        ZEPHYR.add_instance_comm(state, data, "k_pipe_block_put")
        # For now just add a k_sem_give from the tread to the given semaphore, if present.
        # This should work, because sem has to be created externally
        if sem != None:
            ZEPHYR.add_instance_comm(state, sem, "k_sem_give")

        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # size_t k_pipe_read_avail(struct k_pipe *pipe)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_pipe_read_avail(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_pipe_read_avail")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # size_t k_pipe_write_avail(struct k_pipe *pipe)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_pipe_write_avail(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_pipe_write_avail")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void *k_heap_alloc(struct k_heap *h, size_t bytes, k_timeout_t timeout)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.value, SigType.value))
    def k_heap_alloc(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        size = get_argument(cfg, abb, state.call_path, 1)
        timeout = get_argument(cfg, abb, state.call_path, 2)

        ZEPHYR.add_instance_comm(state, data, "k_heap_alloc")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_heap_free(struct k_heap *h, void *mem)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.symbol))
    def k_heap_free(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        #mem = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_instance_comm(state, data, "k_heap_free")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void *k_malloc(size_t size)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.value, ))
    def k_malloc(cfg, abb, state):
        state = state.copy()

        size = get_argument(cfg, abb, state.call_path, 0)

        ZEPHYR.add_comm(state, ZEPHYR.kernel, "k_malloc")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_free(void *ptr)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, ))
    def k_free(cfg, abb, state):
        state = state.copy()

        mem = get_argument(cfg, abb, state.call_path, 0)

        ZEPHYR.add_comm(state, ZEPHYR.kernel, "k_free")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void *k_calloc(size_t nmemb, size_t size)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.value, SigType.value))
    def k_calloc(cfg, abb, state):
        state = state.copy()

        num_elements = get_argument(cfg, abb, state.call_path, 0)
        element_size = get_argument(cfg, abb, state.call_path, 1)

        ZEPHYR.add_comm(state, ZEPHYR.kernel, "k_calloc")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_msgq_cleanup(struct k_msgq *msgq)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol,))
    def k_msgq_cleanup(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_msgq_cleanup")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_msgq_put(struct k_msgq *msgq, const void *data, k_timeout_t timeout)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.symbol, SigType.value))
    def k_msgq_put(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        item = get_argument(cfg, abb, state.call_path, 1, ty=pyllco.Value)
        timeout = get_argument(cfg, abb, state.call_path, 2)

        ZEPHYR.add_instance_comm(state, data, "k_msgq_put")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_msgq_get(struct k_msgq *msgq, void *data, k_timeout_t timeout)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.symbol, SigType.value))
    def k_msgq_get(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        item = get_argument(cfg, abb, state.call_path, 1, ty=pyllco.Value)
        timeout = get_argument(cfg, abb, state.call_path, 2)

        ZEPHYR.add_instance_comm(state, data, "k_msgq_get")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # int k_msgq_peek(struct k_msgq *msgq, void *data)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.symbol))
    def k_msgq_peek(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        item = get_argument(cfg, abb, state.call_path, 1, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_msgq_peek")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_msgq_purge(struct k_msgq *msgq)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol,))
    def k_msgq_purge(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_msgq_purge")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # uint32_t k_msgq_num_free_get(struct k_msgq *msgq)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol,))
    def k_msgq_num_free_get(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_msgq_num_free_get")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

    # void k_msgq_get_attrs(struct k_msgq *msgq, struct k_msgq_attrs *attrs)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol, SigType.symbol))
    def k_msgq_get_attrs(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)
        attributes = get_argument(cfg, abb, state.call_path, 1, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_msgq_get_attrs")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state


    # uint32_t k_msgq_num_used_get(struct k_msgq *msgq)
    @syscall(categories={SyscallCategory.comm},
             signature=(SigType.symbol,))
    def k_msgq_num_used_get(cfg, abb, state):
        state = state.copy()

        data = get_argument(cfg, abb, state.call_path, 0, ty=pyllco.Value)

        ZEPHYR.add_instance_comm(state, data, "k_msgq_num_used_get")
        state.next_abbs = []
        ZEPHYR.add_normal_cfg(cfg, abb, state)

        return state

