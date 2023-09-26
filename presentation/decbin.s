	.align 16
block.1:
    cmpq $0, %rcx
    jg block.23
    jmp block.2

	.align 16
block.2:
    callq print_int
    movq $0, %rax
    jmp conclusion

	.align 16
block.3:
    addq $1, %r9
    jmp block.1

	.align 16
block.4:
    jmp block.3

	.align 16
block.5:
    addq %r8, %rdi
    jmp block.3

	.align 16
block.6:
    movq %rsi, %r8
    jmp block.5

	.align 16
block.7:
    cmpq %r9, %rsi
    jl block.12
    jmp block.8

	.align 16
block.8:
    movq %r10, %r8
    jmp block.5

	.align 16
block.9:
    cmpq $9, %r8
    jl block.11
    jmp block.10

	.align 16
block.10:
    addq $1, %rsi
    jmp block.7

	.align 16
block.11:
    addq %r12, %r10
    addq $1, %r8
    jmp block.9

	.align 16
block.12:
    movq $0, %r8
    movq %r10, %r12
    jmp block.9

	.align 16
block.13:
    movq $1, %r10
    movq $0, %rsi
    jmp block.7

	.align 16
block.14:
    cmpq $0, %r9
    je block.6
    jmp block.13

	.align 16
block.15:
    cmpq %r10, %rcx
    jg block.22
    jmp block.16

	.align 16
block.16:
    movq %r8, %rcx
    movq $1, %r8
    cmpq $0, %rsi
    je block.4
    jmp block.14

	.align 16
block.17:
    addq $1, %r8
    jmp block.15

	.align 16
block.18:
    subq %rdx, %rcx
    cmpq $0, %rcx
    jge block.17
    jmp block.15

	.align 16
block.19:
    movq $0, %rsi
    jmp block.18

	.align 16
block.20:
    cmpq $0, %rcx
    je block.19
    jmp block.18

	.align 16
block.21:
    movq $1, %rsi
    jmp block.20

	.align 16
block.22:
    cmpq $1, %rcx
    je block.21
    jmp block.20

	.align 16
block.23:
    movq $0, %rsi
    movq $0, %r8
    movq $1, %r10
    negq %r10
    jmp block.15

	.align 16
start:
    callq read_int
    movq %rax, %rcx
    movq $0, %rdi
    movq $2, %rdx
    movq $0, %r9
    jmp block.1

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    pushq %r12
    subq $8, %rsp
    movq $65536, %rdi
    movq $16, %rsi
    callq initialize
    movq rootstack_begin(%rip), %r15
    addq $0, %r15
    jmp start

	.align 16
conclusion:
    subq $0, %r15
    addq $8, %rsp
    popq %r12
    popq %rbp
    retq


