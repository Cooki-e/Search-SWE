"""Apply a per-request Landlock filesystem policy before executing answer.sh."""

import ctypes, os, sys
from pathlib import Path


def restrict_answer(input_path, output_dir, temp_dir):
    libc = ctypes.CDLL(None, use_errno=True)
    abi = libc.syscall(444, 0, 0, 1)
    if abi < 1:
        raise RuntimeError("Answer isolation requires Landlock")
    handled = (1 << (15 if abi >= 3 else 14 if abi >= 2 else 13)) - 1

    class Ruleset(ctypes.Structure):
        _fields_ = [("handled_access_fs", ctypes.c_uint64)]

    class Beneath(ctypes.Structure):
        _pack_ = 1
        _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]

    attr = Ruleset(handled)
    rules = libc.syscall(444, ctypes.byref(attr), ctypes.sizeof(attr), 0)
    if rules < 0:
        raise OSError(ctypes.get_errno(), "create answer ruleset")

    def allow(path, rights):
        path = Path(path)
        if not path.exists():
            return
        fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
        try:
            rule = Beneath(rights, fd)
            if libc.syscall(445, rules, 1, ctypes.byref(rule), 0) < 0:
                raise OSError(ctypes.get_errno(), "add answer path")
        finally:
            os.close(fd)

    try:
        readonly = (1 << 0) | (1 << 2) | (1 << 3)
        for path in ["/usr", "/opt", "/etc", "/lib", "/lib64", "/bin", "/sbin", "/sys"]:
            allow(path, readonly)
        allow("/app/answer.sh", (1 << 0) | (1 << 2))
        allow("/app/answer", readonly)
        allow(input_path, 1 << 2)
        allow(output_dir, handled)
        allow(temp_dir, handled)
        for path in ["/dev/null", "/dev/zero"]:
            allow(path, (1 << 1) | (1 << 2))
        for path in ["/dev/urandom", "/dev/random"]:
            allow(path, 1 << 2)
        if libc.prctl(38, 1, 0, 0, 0) < 0:
            raise OSError(ctypes.get_errno(), "no_new_privs")
        if libc.syscall(446, rules, 0) < 0:
            raise OSError(ctypes.get_errno(), "restrict answer")
    finally:
        os.close(rules)


if __name__ == "__main__":
    request, output, temp = sys.argv[1:4]
    restrict_answer(request, str(Path(output).parent), temp)
    os.execv(
        "/app/answer.sh", ["/app/answer.sh", "--input", request, "--output", output]
    )
