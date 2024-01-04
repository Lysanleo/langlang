	.align 16
block.10:
    cmpq $10, %r12
    jl block.17
    jmp block.11

	.align 16
block.11:
    movq $0, %rax
    jmp conclusion

	.align 16
block.12:
    cmpq %r12, %r13
    jl block.16
    jmp block.13

	.align 16
block.13:
    addq $1, %r12
    jmp block.10

	.align 16
block.14:
    addq $1, %r13
    jmp block.12

	.align 16
block.15:
    movq %r12, %rdi
    callq print_int
    jmp block.14

	.align 16
block.16:
    movq %r13, %rcx
    addq %r13, %rcx
    cmpq %r12, %rcx
    je block.15
    jmp block.14

	.align 16
block.17:
    movq $0, %r13
    jmp block.12

	.align 16
start:
    movq $0, %r12
    jmp block.10

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    pushq %r13
    pushq %r12
    subq $0, %rsp
    movq $65536, %rdi
    movq $16, %rsi
    callq initialize
    movq rootstack_begin(%rip), %r15
    addq $0, %r15
    jmp start

	.align 16
conclusion:
    subq $0, %r15
    addq $0, %rsp
    popq %r12
    popq %r13
    popq %rbp
    retq


