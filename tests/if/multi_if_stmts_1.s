	.align 16
block.8:
    movq $0, %rax
    jmp conclusion

	.align 16
block.9:
    movq $1, %rdi
    callq print_int
    jmp block.8

	.align 16
block.10:
    movq $0, %rdi
    callq print_int
    jmp block.8

	.align 16
block.11:
    movq $1, %rcx
    addq $1, %rcx
    cmpq $2, %rcx
    je block.9
    jmp block.10

	.align 16
block.12:
    movq $3, %rdi
    callq print_int
    jmp block.11

	.align 16
block.13:
    movq $2, %rdi
    callq print_int
    jmp block.11

	.align 16
start:
    movq $1, %rcx
    addq $2, %rcx
    cmpq $2, %rcx
    je block.12
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


