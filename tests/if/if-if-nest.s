	.align 16
block.1:
    movq $0, %rax
    jmp conclusion

	.align 16
block.2:
    movq %rcx, %rdi
    callq print_int
    jmp block.1

	.align 16
block.3:
    movq %rcx, %rdi
    callq print_int
    jmp block.1

	.align 16
block.4:
    movq $1, %rcx
    negq %rcx
    movq %rcx, %rdi
    callq print_int
    jmp block.1

	.align 16
block.5:
    cmpq $0, %rcx
    je block.3
    jmp block.4

	.align 16
start:
    movq $2, %rcx
    cmpq $1, %rcx
    je block.2
    jmp block.5

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


