	.align 16
start:
    movq $1, %rdx
    movq $42, %rcx
    addq $7, %rdx
    movq %rdx, %rsi
    addq %rcx, %rsi
    movq %rdx, %rcx
    negq %rcx
    movq %rsi, %rdx
    addq %rcx, %rdx
    movq %rdx, %rdi
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


