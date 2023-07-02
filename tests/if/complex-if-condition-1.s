	.align 16
block.20:
    movq $0, %rax
    jmp conclusion

	.align 16
block.21:
    movq $0, %rdi
    callq print_int
    jmp block.20

	.align 16
block.22:
    movq $1, %rdi
    callq print_int
    jmp block.20

	.align 16
start:
    movq $1, %rcx
    addq $2, %rcx
    movq $3, %rdx
    subq $1, %rdx
    cmpq %rdx, %rcx
    jl block.21
    jmp block.22

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


