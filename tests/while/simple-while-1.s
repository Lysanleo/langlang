	.align 16
block.18:
    cmpq $0, %rcx
    jg block.20
    jmp block.19

	.align 16
block.19:
    movq %rdx, %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.align 16
block.20:
    addq %rcx, %rdx
    subq $1, %rcx
    jmp block.18

	.align 16
start:
    movq $5, %rcx
    movq $0, %rdx
    jmp block.18

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    pushq %r12
    pushq %r13
    subq $0, %rsp
    jmp start

	.align 16
conclusion:
    addq $0, %rsp
    popq %r12
    popq %r13
    popq %rbp
    retq


