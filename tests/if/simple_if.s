	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    subq $16, %rsp
    addq $16, %rsp
    popq %rbp
    retq


