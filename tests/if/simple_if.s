	.align 16
block.15:
    movq %rcx, %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.align 16
block.16:
    addq $2, %rcx
    jmp block.15

	.align 16
block.17:
    addq $10, %rcx
    jmp block.15

	.align 16
block.18:
    cmpq $0, %r12
    je block.16
    jmp block.17

	.align 16
block.19:
    cmpq $2, %r12
    je block.16
    jmp block.17

	.align 16
start:
    callq read_int
    movq %rax, %r12
    callq read_int
    movq %rax, %rcx
    cmpq $1, %r12
    jl block.18
    jmp block.19

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


