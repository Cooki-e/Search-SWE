#define _GNU_SOURCE
#include <errno.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <sched.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

/* The offline builder is unrestricted by this launcher. Online clients,
 * services and their descendants share one logical CPU. Prevent an executable
 * or numerical runtime from expanding that inherited affinity mask. */
int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: search-swe-query-cpu COMMAND [ARG ...]\n");
        return 64;
    }
    cpu_set_t available, selected;
    if (sched_getaffinity(0, sizeof(available), &available) != 0) {
        perror("sched_getaffinity");
        return 70;
    }
    CPU_ZERO(&selected);
    int cpu = 0;
    for (; cpu < CPU_SETSIZE && !CPU_ISSET(cpu, &available); ++cpu) {}
    if (cpu == CPU_SETSIZE) {
        fprintf(stderr, "no permitted query CPU\n");
        return 70;
    }
    CPU_SET(cpu, &selected);
    if (sched_setaffinity(0, sizeof(selected), &selected) != 0) {
        perror("sched_setaffinity");
        return 70;
    }
    /* LLVM OpenMP probes topology by temporarily changing affinity unless
     * disabled explicitly. It must respect the inherited single-CPU mask. */
    if (setenv("KMP_AFFINITY", "disabled", 1) != 0 ||
        setenv("OMP_PROC_BIND", "false", 1) != 0 ||
        unsetenv("GOMP_CPU_AFFINITY") != 0) {
        perror("configure numerical runtime affinity");
        return 70;
    }
#if defined(__x86_64__)
#define NATIVE_AUDIT_ARCH AUDIT_ARCH_X86_64
#elif defined(__aarch64__)
#define NATIVE_AUDIT_ARCH AUDIT_ARCH_AARCH64
#else
#error "query CPU launcher requires a supported native 64-bit architecture"
#endif
    struct sock_filter filter[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, NATIVE_AUDIT_ARCH, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
#if defined(__x86_64__)
        /* x32 has a distinct syscall-number namespace but the same arch tag. */
        BPF_JUMP(BPF_JMP | BPF_JGE | BPF_K, 0x40000000U, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
#endif
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_sched_setaffinity, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog program = {
        .len = (unsigned short)(sizeof(filter) / sizeof(filter[0])),
        .filter = filter,
    };
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0 ||
        prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &program) != 0) {
        perror("install query CPU boundary");
        return 70;
    }
    execvp(argv[1], argv + 1);
    perror("exec query command");
    return 127;
}
