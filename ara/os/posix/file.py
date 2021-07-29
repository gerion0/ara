import os
import pyllco
from dataclasses import dataclass
from ara.graph import SyscallCategory, SigType

from ..os_util import syscall, Arg
from .file_descriptor import create_file_desc_of, FDType
from .posix_utils import IDInstance, register_instance, logger, CurrentSyscallCategories, add_edge_from_self_to, assign_instance_to_return_value

@dataclass(eq = False)
class File(IDInstance):
    path: str # Path to the file

    wanted_attrs = ["name", "path"]
    dot_appearance = {
        "shape": "box",
        "fillcolor": "#08a2e0",
        "style": "filled"
    }

    def __post_init__(self):
        super().__init__()

# Musl libc file access modes for open()
FILE_ACCESS_MODES = dict({
    (0o0, FDType.READ),
    (0o1, FDType.WRITE),
    (0o2, FDType.BOTH),
    # O_SEARCH and O_EXEC equal O_PATH with id 010000000 in musl libc. We do not handle these.
})

# POSIX file access mode identifier.
FAM_IDENTIFIER = dict({
    (FDType.READ, 'O_RDONLY'),
    (FDType.WRITE, 'O_WRONLY'),
    (FDType.BOTH, 'O_RDWR'),
})

class FileSyscalls:

    # Map path -> File object
    # Note: chdir() is not supported and we can not detect multiple open() calls to the same file from different directories.
    files = dict()

    # int open(const char *path, int oflag, ...);
    @syscall(aliases={"open64"}, signal_safe=True,
             categories={SyscallCategory.create, SyscallCategory.comm},
             signature=(Arg('path', hint=SigType.value),
                        Arg('oflag', hint=SigType.value, ty=pyllco.ConstantInt),
                        Arg('mode', hint=SigType.value, optional=True)))
    def open(graph, abb, state, args, va):

        cp = state.call_path
        file = None

        # Detect file access mode.
        fam: FDType = None
        if args.oflag != None:
            fam = [FILE_ACCESS_MODES.get(mode, None) for mode in FILE_ACCESS_MODES.keys()
                    if (args.oflag.get() & 0b11) == mode]
            if len(fam) < 1 or fam[0] == None:
                logger.warning(f"open(): Could not detect file access mode in value {args.oflag.get()}.")
                fam = None
            assert len(fam) == 1
            fam = fam[0]
            assert type(fam) == FDType
        else:
            logger.warning("open(): No file access mode detection because oflag argument is missing!")

        # If Category "create": Create File Object
        if SyscallCategory.create in CurrentSyscallCategories.get():
            if args.path == None:
                logger.warning("open(): Could not get path argument. The File object is now untrackable for interaction open() calls.")
            if args.path in FileSyscalls.files:
                file = FileSyscalls.files[args.path]
                logger.debug(f"open() call to already created File object: {file}")
            else:
                file = File(path=args.path,
                            name=(os.path.basename(args.path) if args.path != None else None)
                )
                
                state = register_instance(file, f"{file.name}", graph, abb, state)
                if args.path != None:
                    FileSyscalls.files[args.path] = file
            # Set the return value to the new filedescriptor (This file)
            assign_instance_to_return_value(va, abb, cp, create_file_desc_of(file, fam if fam != None else FDType.BOTH))

        # If Category "comm": Create edge to the addressed File object
        if SyscallCategory.comm in CurrentSyscallCategories.get():
            file = FileSyscalls.files.get(args.path, None)
            if file != None:
                state = add_edge_from_self_to(state, file, f"open({FAM_IDENTIFIER[fam] if fam != None else ''})")
            else:
                logger.warning(f"open(): File with path {args.path} not found!")

        return state