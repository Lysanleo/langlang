	.align 16
block.15:
    movq $0, %rax
    jmp conclusion

	.align 16
block.16:
    movq $1, %rdi
    callq print_int
    jmp block.15

	.align 16
block.17:
    movq $0, %rdi
    callq print_int
    jmp block.15

	.align 16
start:
    movq $1, %rcx
    addq $1, %rcx
    cmpq $2, %rcx
    je block.16
    jmp block.17

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    subq $0, %rsp
    jmp start

	.align 16
conclusion:
    addq $0, %rsp
    popq %rbp
    retq


