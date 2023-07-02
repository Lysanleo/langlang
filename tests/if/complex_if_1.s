	.align 16
block.21:
    movq $0, %rax
    jmp conclusion

	.align 16
block.22:
    movq $1, %rdi
    callq print_int
    jmp block.21

	.align 16
block.23:
    movq $0, %rdi
    callq print_int
    jmp block.21

	.align 16
start:
    movq $1, %rcx
    addq $1, %rcx
    cmpq $2, %rcx
    je block.22
    jmp block.23

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


