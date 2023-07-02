	.align 16
block.0:
    cmpq $0, %rdx
    jg block.2
    jmp block.1

	.align 16
block.1:
    movq %rcx, %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.align 16
block.2:
    addq %rdx, %rcx
    subq $1, %rdx
    jmp block.0

	.align 16
start:
    movq $5, %rdx
    movq $0, %rcx
    jmp block.0

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


