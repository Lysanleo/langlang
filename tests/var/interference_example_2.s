	.align 16
start:
    movq $1, -48(%rbp)
    movq $42, -72(%rbp)
    movq -48(%rbp), %rax
    movq %rax, -64(%rbp)
    addq $7, -64(%rbp)
    movq -64(%rbp), %rax
    movq %rax, -40(%rbp)
    movq -64(%rbp), %rax
    movq %rax, -80(%rbp)
    movq -72(%rbp), %rax
    addq %rax, -80(%rbp)
    movq -40(%rbp), %rax
    movq %rax, -88(%rbp)
    negq -88(%rbp)
    movq -80(%rbp), %rax
    movq %rax, -56(%rbp)
    movq -88(%rbp), %rax
    addq %rax, -56(%rbp)
    movq -56(%rbp), %rdi
    callq print_int
    movq $0, %rax
    jmp conclusion

	.globl main
	.align 16
main:
    pushq %rbp
    movq %rsp, %rbp
    subq $96, %rsp
    jmp start

	.align 16
conclusion:
    addq $96, %rsp
    popq %rbp
    retq


