	.align 16
block.15:
    movq free_ptr(%rip), %r11
    addq $24, free_ptr(%rip)
    movq $261, 0(%r11)
    movq %r11, 0(%r15)
    movq 0(%r15), %r11
    movq %r12, 8(%r11)
    movq 0(%r15), %r11
    movq 8(%r15), %rax
    movq %rax, 16(%r11)
    movq 0(%r15), %r11
    movq 8(%r11), %rcx
    movq %rcx, %rdi
    callq print_int
    movq 0(%r15), %r11
    movq 16(%r11), %rax
    movq %rax, 0(%r15)
    movq 0(%r15), %r11
    movq 16(%r11), %rcx
    movq %rcx, %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.align 16
block.16:
    movq %r15, %rdi
    movq $24, %rsi
    callq collect
    jmp block.15

	.align 16
block.17:
    movq free_ptr(%rip), %r11
    addq $24, free_ptr(%rip)
    movq $5, 0(%r11)
    movq %r11, 0(%r15)
    movq 0(%r15), %r11
    movq %r13, 8(%r11)
    movq 0(%r15), %r11
    movq %r14, 16(%r11)
    movq 0(%r15), %rax
    movq %rax, 8(%r15)
    movq free_ptr(%rip), %rcx
    movq %rcx, %rdx
    addq $24, %rdx
    movq fromspace_end(%rip), %rcx
    cmpq %rcx, %rdx
    jl block.15
    jmp block.16

	.align 16
block.18:
    movq %r15, %rdi
    movq $24, %rsi
    callq collect
    jmp block.17

	.align 16
start:
    movq $1, %r12
    movq $2, %r13
    movq $3, %r14
    movq free_ptr(%rip), %rcx
    movq %rcx, %rdx
    addq $24, %rdx
    movq fromspace_end(%rip), %rcx
    cmpq %rcx, %rdx
    jl block.17
    jmp block.18

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    pushq %r14
    pushq %r13
    pushq %r12
    subq $8, %rsp
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
    addq $8, %rsp
    popq %r12
    popq %r13
    popq %r14
    popq %rbp
    retq


