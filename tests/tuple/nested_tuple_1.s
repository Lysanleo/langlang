	.align 16
block.72:
    movq free_ptr(%rip), %r11
    addq $16, free_ptr(%rip)
    movq $131, 0(%r11)
    movq %r11, 16(%r15)
    movq 16(%r15), %r11
    movq 8(%r15), %rax
    movq %rax, 8(%r11)
    movq 16(%r15), %rax
    movq %rax, 0(%r15)
    movq 0(%r15), %r11
    movq 8(%r11), %rax
    movq %rax, 8(%r15)
    movq 8(%r15), %r11
    movq 8(%r11), %rcx
    movq %rcx, %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.align 16
block.73:
    movq %r15, %rdi
    movq $16, %rsi
    callq collect
    jmp block.72

	.align 16
block.74:
    movq free_ptr(%rip), %r11
    addq $16, free_ptr(%rip)
    movq $3, 0(%r11)
    movq %r11, 8(%r15)
    movq 8(%r15), %r11
    movq %rbx, 8(%r11)
    movq free_ptr(%rip), %rcx
    addq $16, %rcx
    movq fromspace_end(%rip), %rdx
    cmpq %rdx, %rcx
    jl block.72
    jmp block.73

	.align 16
block.75:
    movq %r15, %rdi
    movq $16, %rsi
    callq collect
    jmp block.74

	.align 16
start:
    movq $42, %rbx
    movq free_ptr(%rip), %rcx
    addq $16, %rcx
    movq fromspace_end(%rip), %rdx
    cmpq %rdx, %rcx
    jl block.74
    jmp block.75

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
    movq $0, 16(%r15)
    addq $24, %r15
    jmp start

	.align 16
conclusion:
    subq $24, %r15
    addq $0, %rsp
    popq %r14
    popq %rbx
    popq %r13
    popq %r12
    popq %rbp
    retq


