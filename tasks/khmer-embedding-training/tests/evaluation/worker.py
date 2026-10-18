#!/usr/bin/env python3
"""Run the fixed checkpoint evaluator with inherited network restrictions."""
import ctypes
import errno
import os
import runpy
import sys
import socket
from pathlib import Path

libc = ctypes.CDLL(None, use_errno=True)
abi = libc.syscall(444, 0, 0, 1)
if abi >= 4:
    class Ruleset(ctypes.Structure):
        _fields_ = [("handled_access_fs", ctypes.c_uint64),
                    ("handled_access_net", ctypes.c_uint64)]
    attr = Ruleset(0, 3)
    fd = libc.syscall(444, ctypes.byref(attr), ctypes.sizeof(attr), 0)
    if fd < 0:
        raise OSError(ctypes.get_errno(), "create network ruleset")
    try:
        if libc.prctl(38, 1, 0, 0, 0) < 0 or libc.syscall(446, fd, 0) < 0:
            raise OSError(ctypes.get_errno(), "restrict network")
    finally:
        os.close(fd)
else:
    # Older kernels lack Landlock networking. Deny the network syscalls with
    # seccomp before loading any checkpoint; children inherit the filter.
    sec = ctypes.CDLL("libseccomp.so.2", use_errno=True)
    sec.seccomp_init.argtypes = [ctypes.c_uint32]
    sec.seccomp_init.restype = ctypes.c_void_p
    sec.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    sec.seccomp_syscall_resolve_name.restype = ctypes.c_int
    sec.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    sec.seccomp_rule_add.restype = ctypes.c_int
    sec.seccomp_load.argtypes = [ctypes.c_void_p]
    sec.seccomp_load.restype = ctypes.c_int
    sec.seccomp_release.argtypes = [ctypes.c_void_p]
    context = sec.seccomp_init(0x7fff0000)  # SCMP_ACT_ALLOW
    if not context:
        raise RuntimeError("Cannot create evaluator seccomp filter")
    try:
        # CUDA uses local/kernel sockets during initialization. Deny internet
        # socket creation while retaining AF_UNIX/AF_NETLINK driver IPC.
        class Compare(ctypes.Structure):
            _fields_ = [("arg", ctypes.c_uint), ("op", ctypes.c_int),
                        ("a", ctypes.c_uint64), ("b", ctypes.c_uint64)]
        sec.seccomp_rule_add_array.argtypes = [
            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint,
            ctypes.POINTER(Compare)]
        sec.seccomp_rule_add_array.restype = ctypes.c_int
        for family in range(46):
            if family in (socket.AF_UNIX, socket.AF_NETLINK):
                continue
            comparison = Compare(0, 4, family, 0)  # SCMP_CMP_EQ
            number = sec.seccomp_syscall_resolve_name(b"socket")
            if sec.seccomp_rule_add_array(context, 0x00050000 | errno.EPERM,
                                         number, 1, ctypes.byref(comparison)) != 0:
                raise RuntimeError("Cannot restrict evaluator socket family")
        for name in [b"io_uring_setup", b"io_uring_enter", b"io_uring_register"]:
            number = sec.seccomp_syscall_resolve_name(name)
            if number < 0 or sec.seccomp_rule_add(context, 0x00050000 | errno.EPERM, number, 0) != 0:
                raise RuntimeError("Cannot restrict evaluator network syscall")
        if sec.seccomp_load(context) != 0:
            raise RuntimeError("Cannot activate evaluator network restrictions")
    finally:
        sec.seccomp_release(context)
sys.path.insert(0, str(Path(__file__).resolve().parent))
runpy.run_path(str(Path(__file__).with_name("evaluator.py")), run_name="__main__")
