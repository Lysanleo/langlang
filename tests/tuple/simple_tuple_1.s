	.align 16
block.20:
    movq free_ptr(%rip), %r11
    addq $16, free_ptr(%rip)
    movq $131, 0(%r11)
    movq %r11, 0(%r15)
    movq 0(%r15), %r11
    movq 8(%r15), %rax
    movq %rax, 8(%r11)
    movq 0(%r15), %r11
    movq 8(%r11), %rax
    movq %rax, 0(%r15)
    movq 0(%r15), %r11
    movq 8(%r11), %rcx
    movq %rcx, %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.align 16
block.21:
    movq %r15, %rdi
    movq $16, %rsi
    callq collect
    jmp block.20

	.align 16
block.22:
    movq free_ptr(%rip), %r11
    addq $16, free_ptr(%rip)
    movq $3, 0(%r11)
    movq %r11, 0(%r15)
    movq 0(%r15), %r11
    movq %rbx, 8(%r11)
    movq 0(%r15), %rax
    movq %rax, 8(%r15)
    movq free_ptr(%rip), %rcx
    movq %rcx, %rdx
    addq $16, %rdx
    movq fromspace_end(%rip), %rcx
    cmpq %rcx, %rdx
    jl block.20
    jmp block.21

	.align 16
block.23:
    movq %r15, %rdi
    movq $16, %rsi
    callq collect
    jmp block.22

	.align 16
start:
    movq $42, %rbx
    movq free_ptr(%rip), %rcx
    addq $16, %rcx
    movq fromspace_end(%rip), %rdx
    cmpq %rdx, %rcx
    jl block.22
    jmp block.23

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    pushq %r12
    pushq %rbx
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
    popq %rbx
    popq %r12
    popq %rbp
    retq


