	.align 16
block.9:
    movq %rcx, %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.align 16
block.10:
    addq $2, %rcx
    jmp block.9

	.align 16
block.11:
    addq $10, %rcx
    jmp block.9

	.align 16
block.12:
    cmpq $0, %rdx
    je block.10
    jmp block.11

	.align 16
block.13:
    cmpq $2, %rdx
    je block.10
    jmp block.11

	.align 16
start:
    callq read_int
    movq %rax, %rdx
    callq read_int
    movq %rax, %rcx
    cmpq $1, %rdx
    jl block.12
    jmp block.13

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


