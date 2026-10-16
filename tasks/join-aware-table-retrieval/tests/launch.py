"""Trusted child bootstrap, installed read-only outside the private tests directory."""
import ctypes
import os
import resource
import sys

assert os.getuid() == 10001
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
resource.setrlimit(resource.RLIMIT_NPROC, (512, 512))
resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024**3, 8 * 1024**3))
if ctypes.CDLL(None, use_errno=True).prctl(38, 1, 0, 0, 0) != 0:
    raise OSError('Could not set no_new_privs')
os.execv(sys.argv[1], sys.argv[1:])
