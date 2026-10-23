"""Drop privileges and prohibit network connections in submitted processes."""
import ctypes
import errno
import os
import sys


class ArgCompare(ctypes.Structure):
    _fields_ = [("arg", ctypes.c_uint), ("op", ctypes.c_int),
                ("datum_a", ctypes.c_uint64), ("datum_b", ctypes.c_uint64)]


def main():
    # libseccomp resolves native syscall numbers; inherited by every child.
    lib = ctypes.CDLL("libseccomp.so.2", use_errno=True)
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_rule_add_array.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int,
                                         ctypes.c_uint, ctypes.POINTER(ArgCompare)]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    ctx = lib.seccomp_init(0x7fff0000)  # SCMP_ACT_ALLOW
    if not ctx:
        raise RuntimeError("seccomp initialization failed")
    try:
        # CUDA uses local UNIX sockets. Permit that domain only; no Internet,
        # netlink or packet sockets. Popen closes inherited unrelated FDs.
        not_unix = ArgCompare(0, 1, 1, 0)  # domain != AF_UNIX, SCMP_CMP_NE
        for name in (b"socket", b"socketpair"):
            number = lib.seccomp_syscall_resolve_name(name)
            if number < 0 or lib.seccomp_rule_add_array(ctx, 0x50000 | errno.EPERM, number, 1, ctypes.byref(not_unix)) != 0:
                raise RuntimeError("seccomp socket-domain rule failed")
        for name in (b"io_uring_setup",):
            number = lib.seccomp_syscall_resolve_name(name)
            if number < 0 or lib.seccomp_rule_add(ctx, 0x50000 | errno.EPERM, number, 0) != 0:
                raise RuntimeError("seccomp rule failed")
        os.setgroups([])
        os.setgid(10001)
        os.setuid(10001)
        if lib.seccomp_load(ctx) != 0:
            raise RuntimeError("seccomp load failed")
    finally:
        lib.seccomp_release(ctx)
    os.execvpe(sys.argv[1], sys.argv[1:], os.environ)


if __name__ == "__main__":
    main()
