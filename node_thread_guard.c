#define _GNU_SOURCE
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <errno.h>
typedef void* napi_env;
typedef void* napi_value;
extern int napi_throw_error(napi_env,const char*,const char*);
__attribute__((visibility("default"))) napi_value napi_register_module_v1(napi_env env,napi_value exports){
 struct sock_filter code[]={
  BPF_STMT(BPF_LD|BPF_W|BPF_ABS,4),BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,0xc000003e,1,0),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_KILL_PROCESS),
  BPF_STMT(BPF_LD|BPF_W|BPF_ABS,0),
  BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,56,3,0),BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,57,2,0),BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,58,1,0),BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,435,0,1),
  BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|EPERM),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW)};
 struct sock_fprog prog={sizeof(code)/sizeof(code[0]),code};
 if(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)!=0 || syscall(SYS_seccomp,SECCOMP_SET_MODE_FILTER,SECCOMP_FILTER_FLAG_TSYNC,&prog)!=0){napi_throw_error(env,0,"node_thread_lock_failed");return 0;}
 return exports;
}
