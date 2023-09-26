	.align 16
block.33:
    movq free_ptr(%rip), %r11
    addq $32, free_ptr(%rip)
    movq $7, 0(%r11)
    movq %r11, 0(%r15)
    movq 0(%r15), %r11
    movq %rbx, 8(%r11)
    movq 0(%r15), %r11
    movq %r12, 16(%r11)
    movq 0(%r15), %r11
    movq %r13, 24(%r11)
    movq 0(%r15), %rax
    movq %rax, 8(%r15)
    movq $3, %rcx
    movq %rcx, %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.align 16
block.34:
    movq %r15, %rdi
    movq $32, %rsi
    callq collect
    jmp block.33

	.align 16
start:
    movq $1, %rbx
    movq $2, %r12
    movq $3, %r13
    movq free_ptr(%rip), %rcx
    addq $32, %rcx
    movq fromspace_end(%rip), %rdx
    cmpq %rdx, %rcx
    jl block.33
    jmp block.34

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    pushq %r12
    pushq %r13
    pushq %rbx
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
    popq %rbx
    popq %r13
    popq %r12
    popq %rbp
    retq


