	.align 16
start:
    callq read_int
    movq %rax, %r12
    callq read_int
    movq %rax, %rcx
    movq %r12, %rdx
    addq %rcx, %rdx
    movq %rdx, %rcx
    addq $42, %rcx
    movq %rcx, %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    pushq %r12
    subq $8, %rsp
    jmp start

	.align 16
conclusion:
    addq $8, %rsp
    popq %r12
    popq %rbp
    retq


