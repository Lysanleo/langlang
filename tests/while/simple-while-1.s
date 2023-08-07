	.align 16
block.18:
    cmpq $0, %rdx
    jg block.20
    jmp block.19

	.align 16
block.19:
    movq %rcx, %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.align 16
block.20:
    addq %rdx, %rcx
    subq $1, %rdx
    jmp block.18

	.align 16
start:
    movq $5, %rdx
    movq $0, %rcx
    jmp block.18

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    pushq %r13
    pushq %r12
    subq $0, %rsp
    jmp start

	.align 16
conclusion:
    addq $0, %rsp
    popq %r13
    popq %r12
    popq %rbp
    retq


