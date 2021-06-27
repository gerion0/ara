from .step import Step
from .option import Option, Bool
from ara.os.os_util import assign_id
from ara.graph import SyscallCategory
from ara.os.posix.posix_utils import MainThread, PosixOptions, StaticInitSyscalls
from ara.os.posix.thread import Thread
from ara.os.posix.posix import POSIX

class POSIXInit(Step):
    """Initializes the POSIX OS Model."""

    # Options for the POSIX OS Model
    enable_static_init_detection = Option(
        name="enable_static_init_detection",
        help="Toggle detection of PTHREAD_MUTEX_INITIALIZER. "
             "Sometimes it is useful to disable this feature. "
             "E.g. if the value analyzer can not retrieve the Mutex handle. "
             "In this case every Mutex interaction call creates a new useless Mutex in the Instance Graph.",
        ty=Bool(),
        default_value=True)

    enable_musl_syscalls = Option(
        name="enable_musl_syscalls",
        help="Toggle detection of native syscalls (e.g. Linux Syscalls) in the musl libc. "
             "Deactivating this feature will degrade the calls __syscall0, __syscall1, ... to stubs. "
             "In combination with the --no-stubs option the deactivation of this option will speed up the analysis. "
             "This feature can be pretty time intensive.",
        ty=Bool(),
        default_value=False)
    

    def get_single_dependencies(self):
        return []

    def register_default_instance(self, inst, label: str):
        """Writes a new default instance to the InstanceGraph.
        
        E.g. the Main Thread is available in all programs.
        """
        instances = self._graph.instances
        v = instances.add_vertex()
        inst.vertex = v
        instances.vp.obj[v] = inst
        instances.vp.label[v] = label

        instances.vp.branch[v] = False
        instances.vp.loop[v] = False
        instances.vp.recursive[v] = False
        instances.vp.after_scheduler[v] = False
        instances.vp.usually_taken[v] = True
        instances.vp.unique[v] = True

        # The following values are not applicable
        instances.vp.soc[v] = 0
        instances.vp.llvm_soc[v] = 0
        instances.vp.file[v] = "N/A"
        instances.vp.line[v] = 0
        instances.vp.specialization_level[v] = "N/A"

        assign_id(instances, v)

    def run(self):
        
        # Generate POSIX Main Thread
        assert self._graph.instances != None, "Missing instance graph!"
        assert self._graph.cfg != None, "Missing control flow graph!"
        main_thread = Thread(entry_abb = None,
                             function = "main",
                             sched_priority="<default>",
                             sched_policy="<default>",
                             inherited_sched_attr=None,
                             name="Main Thread",
                             is_regular=False
        )
        self.register_default_instance(main_thread, "Main Thread")
        MainThread.set(main_thread)

        # Set OS Model options
        PosixOptions.enable_static_init_detection = self.enable_static_init_detection.get()
        PosixOptions.enable_musl_syscalls = self.enable_musl_syscalls.get()

        # Disable SyscallCategory.create in StaticInitSyscalls
        # if static init detection is disabled.
        if not PosixOptions.enable_static_init_detection:
            for comm_func in StaticInitSyscalls.get_comms():
                comm_func.categories = {SyscallCategory.comm}

        # Set musl syscall detection functions to stubs
        # if musl syscalls are disabled.
        if not PosixOptions.enable_musl_syscalls:
            for i in range(0, 7):
                getattr(POSIX, "_musl_syscall" + str(i)).is_stub = True