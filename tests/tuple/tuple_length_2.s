	.align 16
block.25:
    movq free_ptr(%rip), %r11
    addq $32, free_ptr(%rip)
    movq $7, 0(%r11)
    movq %r11, 8(%r15)
    movq 8(%r15), %r11
    movq %r13, 8(%r11)
    movq 8(%r15), %r11
    movq %r12, 16(%r11)
    movq 8(%r15), %r11
    movq %rbx, 24(%r11)
    movq 8(%r15), %rax
    movq %rax, 0(%r15)
    movq $3, %rcx
    movq %rcx, %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.align 16
block.26:
    movq %r15, %rdi
    movq $32, %rsi
    callq collect
    jmp block.25

	.align 16
start:
    movq $1, %r13
    movq $2, %r12
    movq $3, %rbx
    movq free_ptr(%rip), %rcx
    movq %rcx, %rdx
    addq $32, %rdx
    movq fromspace_end(%rip), %rcx
    cmpq %rcx, %rdx
    jl block.25
    jmp block.26

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    pushq %r13
    pushq %r12
    pushq %rbx
    subq $8, %rsp
    movq $65536, %rdi
    movq $16, %rsi
    callq initialize
    movq rootstack_begin(%rip), %r15
    movq $0, 0(%r15)
    movq $0, 0(%r15)
    movq $0, 8(%r15)
    movq $0, 0(%r15)
    movq $0, 0(%r15)
    movq $0, 0(%r15)
    movq $0, 0(%r15)
    movq $0, 0(%r15)
    movq $0, 8(%r15)
    addq $16, %r15
    jmp start

	.align 16
conclusion:
    subq $16, %r15
    addq $8, %rsp
    popq %rbx
    popq %r12
    popq %r13
    popq %rbp
    retq


