	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    subq $16, %rsp
    movq $10, -8(%rbp)
    negq -8(%rbp)
    movq -8(%rbp), %rax
    movq %rax, -16(%rbp)
    addq $42, -16(%rbp)
    movq -16(%rbp), %rax
    movq %rax, -24(%rbp)
    addq $10, -24(%rbp)
    movq -24(%rbp), %rdi
    callq print_int
    addq $16, %rsp
    popq %rbp
    retq


