	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    subq $16, %rsp
    movq $10, -8(%rbp)
    addq $10, -8(%rbp)
    movq $0, %rdi
    callq print_int
    addq $16, %rsp
    popq %rbp
    retq


