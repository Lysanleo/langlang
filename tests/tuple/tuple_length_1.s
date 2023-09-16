	.align 16
block.36:
    movq free_ptr(%rip), %r11
    addq $40, free_ptr(%rip)
    movq $9, 0(%r11)
    movq %r11, 0(%r15)
    movq 0(%r15), %r11
    movq %r13, 8(%r11)
    movq 0(%r15), %r11
    movq %r14, 16(%r11)
    movq 0(%r15), %r11
    movq %r12, 24(%r11)
    movq 0(%r15), %r11
    movq %rbx, 32(%r11)
    movq 0(%r15), %rax
    movq %rax, 8(%r15)
    movq $4, %rcx
    movq %rcx, %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.align 16
block.37:
    movq %r15, %rdi
    movq $40, %rsi
    callq collect
    jmp block.36

	.align 16
start:
    movq $1, %r13
    movq $2, %r14
    movq $3, %r12
    movq $4, %rbx
    movq free_ptr(%rip), %rcx
    movq %rcx, %rdx
    addq $40, %rdx
    movq fromspace_end(%rip), %rcx
    cmpq %rcx, %rdx
    jl block.36
    jmp block.37

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    pushq %r13
    pushq %r14
    pushq %r12
    pushq %rbx
    subq $0, %rsp
    movq $65536, %rdi
    movq $16, %rsi
    callq initialize
    movq rootstack_begin(%rip), %r15
    movq $0, 0(%r15)
    movq $0, 0(%r15)
    movq $0, 0(%r15)
    movq $0, 0(%r15)
    movq $0, 0(%r15)
    movq $0, 0(%r15)
    movq $0, 0(%r15)
    movq $0, 0(%r15)
    movq $0, 0(%r15)
    movq $0, 8(%r15)
    movq $0, 8(%r15)
    addq $16, %r15
    jmp start

	.align 16
conclusion:
    subq $16, %r15
    addq $0, %rsp
    popq %rbx
    popq %r12
    popq %r14
    popq %r13
    popq %rbp
    retq


