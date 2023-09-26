	.align 16
block.47:
    movq free_ptr(%rip), %r11
    addq $40, free_ptr(%rip)
    movq $9, 0(%r11)
    movq %r11, 8(%r15)
    movq 8(%r15), %r11
    movq %r12, 8(%r11)
    movq 8(%r15), %r11
    movq %rbx, 16(%r11)
    movq 8(%r15), %r11
    movq %r13, 24(%r11)
    movq 8(%r15), %r11
    movq %r14, 32(%r11)
    movq 8(%r15), %rax
    movq %rax, 0(%r15)
    movq 0(%r15), %r11
    movq 8(%r11), %rcx
    movq %rcx, %rdi
    callq print_int
    movq 0(%r15), %r11
    movq 16(%r11), %rcx
    movq %rcx, %rdi
    callq print_int
    movq 0(%r15), %r11
    movq 24(%r11), %rcx
    movq %rcx, %rdi
    callq print_int
    movq 0(%r15), %r11
    movq 32(%r11), %rcx
    movq %rcx, %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.align 16
block.48:
    movq %r15, %rdi
    movq $40, %rsi
    callq collect
    jmp block.47

	.align 16
start:
    movq $1, %r12
    movq $2, %rbx
    movq $3, %r13
    movq $4, %r14
    movq free_ptr(%rip), %rcx
    addq $40, %rcx
    movq fromspace_end(%rip), %rdx
    cmpq %rdx, %rcx
    jl block.47
    jmp block.48

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    pushq %r12
    pushq %r13
    pushq %rbx
    pushq %r14
    subq $0, %rsp
    movq $65536, %rdi
    movq $16, %rsi
    callq initialize
    movq rootstack_begin(%rip), %r15
    movq $0, 0(%r15)
    movq $0, 8(%r15)
    addq $16, %r15
    jmp start

	.align 16
conclusion:
    subq $16, %r15
    addq $0, %rsp
    popq %r14
    popq %rbx
    popq %r13
    popq %r12
    popq %rbp
    retq


