	.align 16
block.2:
    movq $0, %rax
    jmp conclusion

	.align 16
block.3:
    movq $1, %rdi
    callq print_int
    jmp block.2

	.align 16
block.4:
    movq $0, %rdi
    callq print_int
    jmp block.2

	.align 16
block.5:
    movq $1, %rcx
    addq $1, %rcx
    cmpq $2, %rcx
    je block.3
    jmp block.4

	.align 16
block.6:
    movq $3, %rdi
    callq print_int
    jmp block.5

	.align 16
block.7:
    movq $2, %rdi
    callq print_int
    jmp block.5

	.align 16
start:
    movq $1, %rcx
    addq $2, %rcx
    cmpq $2, %rcx
    je block.6
    jmp block.7

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
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
    popq %rbp
    retq


