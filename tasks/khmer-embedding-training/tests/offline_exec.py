#!/usr/bin/env python3
"""Apply inherited offline execution restrictions without blocking CUDA IPC."""
import ctypes
import errno
import os
import socket
import sys


def restrict_network():
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
        raise OSError(ctypes.get_errno(), "no_new_privs")
    sec = ctypes.CDLL("libseccomp.so.2", use_errno=True)
    sec.seccomp_init.argtypes = [ctypes.c_uint32]
    sec.seccomp_init.restype = ctypes.c_void_p
    sec.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    sec.seccomp_syscall_resolve_name.restype = ctypes.c_int
    sec.seccomp_rule_add.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_int,
        ctypes.c_uint,
    ]
    sec.seccomp_rule_add.restype = ctypes.c_int
    sec.seccomp_load.argtypes = [ctypes.c_void_p]
    sec.seccomp_load.restype = ctypes.c_int
    sec.seccomp_release.argtypes = [ctypes.c_void_p]

    class Compare(ctypes.Structure):
        _fields_ = [
            ("arg", ctypes.c_uint),
            ("op", ctypes.c_int),
            ("a", ctypes.c_uint64),
            ("b", ctypes.c_uint64),
        ]

    sec.seccomp_rule_add_array.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_int,
        ctypes.c_uint,
        ctypes.POINTER(Compare),
    ]
    sec.seccomp_rule_add_array.restype = ctypes.c_int
    context = sec.seccomp_init(0x7FFF0000)
    if not context:
        raise RuntimeError("Cannot create offline seccomp filter")
    try:
        # Only local/kernel IPC is needed by the CUDA driver.
        # The two inequalities also reject future/unknown network families.
        socket_number = sec.seccomp_syscall_resolve_name(b"socket")
        comparisons = [Compare(0, 3, 0, 0), Compare(0, 5, 17, 0)]
        comparisons.extend(Compare(0, 4, family, 0) for family in range(2, 16))
        for comparison in comparisons:
            if (
                sec.seccomp_rule_add_array(
                    context,
                    0x00050000 | errno.EPERM,
                    socket_number,
                    1,
                    ctypes.byref(comparison),
                )
                != 0
            ):
                raise RuntimeError("Cannot restrict socket families")
        for name in (b"io_uring_setup", b"io_uring_enter", b"io_uring_register"):
            number = sec.seccomp_syscall_resolve_name(name)
            if (
                number < 0
                or sec.seccomp_rule_add(context, 0x00050000 | errno.EPERM, number, 0)
                != 0
            ):
                raise RuntimeError("Cannot restrict network syscall")
        if sec.seccomp_load(context) != 0:
            raise RuntimeError("Cannot activate offline seccomp filter")
    finally:
        sec.seccomp_release(context)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Expected executable and arguments")
    restrict_network()
    os.execv(sys.argv[1], sys.argv[1:])
