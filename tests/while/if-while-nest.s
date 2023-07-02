	.align 16
block.1:
    cmpq $10, %r12
    jl block.8
    jmp block.2

	.align 16
block.2:
    movq $0, %rax
    jmp conclusion

	.align 16
block.3:
    cmpq %r12, %rcx
    jl block.7
    jmp block.4

	.align 16
block.4:
    addq $1, %r12
    jmp block.1

	.align 16
block.5:
    movq %r12, %rdi
    callq print_int
    movq %r12, %rcx
    jmp block.3

	.align 16
block.6:
    addq $1, %rcx
    jmp block.3

	.align 16
block.7:
    movq %rcx, %rdx
    addq %rcx, %rdx
    cmpq %r12, %rdx
    je block.5
    jmp block.6

	.align 16
block.8:
    movq $0, %rcx
    jmp block.3

	.align 16
start:
    movq $0, %r12
    jmp block.1

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


