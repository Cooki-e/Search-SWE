#!/usr/bin/env python3
"""Real IPC/xattr regressions; run only in a fresh disposable verifier container.

Use --expect-vulnerable solely as a negative control against the old image.
No corpus, model source or hidden query is used by these probes.
"""

import argparse
import ctypes
import json
import os
import subprocess
import sys
from pathlib import Path

PROBE = r'''
use std::{env, fs, process::Command};
use std::os::unix::process::ExitStatusExt;
extern "C" {
    fn shmget(key: i32, size: usize, flags: i32) -> i32;
    fn shmat(id: i32, addr: *const u8, flags: i32) -> *mut u8;
    fn shmdt(addr: *const u8) -> i32;
    fn getxattr(path: *const u8, name: *const u8, out: *mut u8, size: usize) -> isize;
    fn syscall(number: i64, ...) -> i64;
    fn __errno_location() -> *mut i32;
}
fn denied(value: i64) {
    assert_eq!(value, -1, "operation unexpectedly allowed");
    assert_eq!(unsafe { *__errno_location() }, 1, "expected EPERM");
}
fn main() {
    let args: Vec<String> = env::args().collect();
    if args[1] == "compat" {
        // A harmless i386 getpid must not bypass the native syscall filter.
        unsafe { core::arch::asm!("int 0x80", inlateout("eax") 20u32 => _, options(nostack)); }
        return;
    }
    let legacy = args[2] == "legacy";
    if !legacy {
        // Valid create calls: these would actually allocate persistent objects.
        denied(unsafe { shmget(0, 4096, 0o1600) } as i64);
        denied(unsafe { syscall(64, 0i64, 1i64, 0o1600i64) }); // semget
        denied(unsafe { syscall(68, 0i64, 0o1600i64) }); // msgget
        denied(unsafe { syscall(240, b"bm25-probe\0".as_ptr(), 0o102i64, 0o600i64, 0i64) });
        denied(unsafe { syscall(0x40000000 | 39) }); // x32 getpid
        // No i386 child can escape after fork + exec either.
        let status = Command::new(&args[0]).arg("compat").status().unwrap();
        assert_eq!(status.signal(), Some(31), "compatibility ABI must be killed");
        // The filter also follows ordinary Rust worker threads.
        std::thread::spawn(|| denied(unsafe { shmget(0, 4096, 0o1600) } as i64)).join().unwrap();
        for number in [191, 194, 248, 249, 250, 425, 426, 427, 463, 464, 465, 466] {
            denied(unsafe { syscall(number, 0i64, 0i64, 0i64, 0i64, 0i64, 0i64) });
        }
    }
    if args[1] == "compile" { return; }
    if args[1] == "index" {
        fs::write("/work/index/marker", b"x").unwrap();
        if legacy {
            let id = unsafe { shmget(0, 4096, 0o1600) };
            assert!(id >= 0);
            let ptr = unsafe { shmat(id, std::ptr::null(), 0) };
            assert_ne!(ptr as isize, -1);
            unsafe { std::ptr::write_bytes(ptr, 42, 4096); assert_eq!(shmdt(ptr), 0); }
            println!("{id}");
        }
        return;
    }
    // Both fresh search processes must still reconstruct ordinary index state.
    assert_eq!(fs::read("/work/index/marker").unwrap(), b"x");
    let id = args[3].parse().unwrap();
    let ptr = unsafe { shmat(id, std::ptr::null(), 0) };
    if legacy {
        assert_ne!(ptr as isize, -1);
        assert!(unsafe { std::slice::from_raw_parts(ptr, 4096) }.iter().all(|&x| x == 42));
        assert_eq!(unsafe { shmdt(ptr) }, 0);
    } else { denied(ptr as i64); }
    let mut bytes = [0u8; 2048];
    // Outside-index metadata needs syscall confinement as well as index checks.
    let length = unsafe { getxattr(b"/tmp/bm25-xattr\0".as_ptr(),
        b"user.hidden\0".as_ptr(), bytes.as_mut_ptr(), bytes.len()) };
    if legacy { assert_eq!(length, 2048); assert_eq!(bytes, [42; 2048]); }
    else { denied(length as i64); }
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect-vulnerable", action="store_true")
    legacy = parser.parse_args().expect_vulnerable
    if os.geteuid() != 0 or not Path("/.dockerenv").exists():
        raise RuntimeError("Use a fresh disposable verifier container, never the host")
    sys.path.insert(0, "/tests")
    from benchmark import index_bytes
    from grader import ENV, kill_submission_processes, own_tree

    Path("/work").mkdir(mode=0o711)
    index = Path("/work/index")
    index.mkdir()
    os.chown(index, 10001, 10001)
    Path("/tmp/probe.rs").write_text(PROBE)
    binary = "/work/bm25-search"
    subprocess.run(["/opt/rust/bin/rustc", "/tmp/probe.rs", "-o", binary], check=True)
    os.chmod(binary, 0o555)
    outside = Path("/tmp/bm25-xattr")
    outside.write_bytes(b"x")
    os.setxattr(outside, "user.hidden", bytes([42]) * 2048)
    os.chmod(outside, 0o444)

    def run(mode, *extra):
        try:
            return subprocess.run([sys.executable, "/tests/isolate.py", mode, binary, mode,
                                   "legacy" if legacy else "blocked", *extra],
                                  check=True, text=True, capture_output=True, env=ENV, timeout=20)
        except subprocess.CalledProcessError as error:
            print(error.stderr, file=sys.stderr)
            raise
        finally:
            kill_submission_processes()

    libc = ctypes.CDLL(None, use_errno=True)
    shm_id = None
    try:
        if not legacy:
            run("compile")
        result = run("index")  # indexer exits; cleanup cannot remove SysV state
        assert index_bytes(index) == 1
        own_tree(index, 0, readonly=True)
        if legacy:
            shm_id = int(result.stdout)
        else:
            # A pre-existing readable segment must also be inaccessible.
            shm_id = libc.shmget(0, 4096, 0o1666)
            assert shm_id >= 0, ctypes.get_errno()
        for _ in range(2):
            run("search", str(shm_id))
        (index / "nested").mkdir()
        for path in [index, index / "nested", index / "marker"]:
            os.setxattr(path, "user.hidden", bytes([42]) * 2048)
            own_tree(index, 0, readonly=True)
            try:
                if legacy:
                    assert index_bytes(index) == 1
                else:
                    try:
                        index_bytes(index)
                    except ValueError as error:
                        assert "extended attributes" in str(error)
                    else:
                        raise AssertionError(f"Uncounted xattr accepted: {path}")
            finally:
                os.removexattr(path, "user.hidden")
        print(json.dumps({"expected_vulnerable": legacy, "index_bytes": 1,
                          "shared_memory_bytes": 4096, "fresh_search_processes": 2,
                          "xattr_payload_bytes": 2048, "xattr_locations": ["root", "directory", "file"],
                          "persistent_state_regression": "passed"}))
    finally:
        kill_submission_processes()
        if shm_id is not None:
            if legacy:
                # The old indexer owns this object. Drop to its UID to remove it.
                subprocess.run([sys.executable, "-c", "import ctypes,os,sys; os.setgroups([]); "
                                "os.setgid(10001); os.setuid(10001); "
                                "assert ctypes.CDLL(None).shmctl(int(sys.argv[1]),0,None)==0", str(shm_id)],
                               check=True)
            else:
                assert libc.shmctl(shm_id, 0, None) == 0


if __name__ == "__main__":
    main()
