	.align 16
block.26:
    movq $0, %rax
    jmp conclusion

	.align 16
block.27:
    movq $0, %rdi
    callq print_int
    jmp block.26

	.align 16
block.28:
    movq $1, %rdi
    callq print_int
    jmp block.26

	.align 16
start:
    movq $1, %rcx
    addq $2, %rcx
    movq $3, %rdx
    subq $1, %rdx
    cmpq %rdx, %rcx
    jl block.27
    jmp block.28

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


