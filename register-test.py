import os
import sys
import compiler_register_allocator as cra
from compiler import Compiler
from sys import platform
from ast import *
from dataclasses import dataclass
from x86_ast import *

# compiler = cra.Compiler()
compiler = cra.Compiler()

def print_ia_map(instrs, ia_map):
    instrs = instrs['main'] if isinstance(instrs, dict) else instrs
    for i in instrs:
        print(f"{i}                     {ia_map[i]}")

tracing = False

def enable_tracing():
    global tracing
    tracing = True

def trace(msg):
    if tracing:
        print(msg, file=sys.stderr)
        
def trace_ast_and_concrete(ast):
    trace("concrete syntax:")
    trace(ast)
    trace("")
    trace("AST:")
    trace(repr(ast))

def compile(compiler, program_filename):
    program_root = os.path.splitext(program_filename)[0]
    with open(program_filename) as source:
        program = parse(source.read())

    print(program)
    trace('\n# remove complex\n')
    program = compiler.remove_complex_operands(program)
    trace_ast_and_concrete(program)

    trace('\n# select instructions\n')
    pseudo_x86 = compiler.select_instructions(program)
    trace_ast_and_concrete(pseudo_x86)

    trace('\n# assign homes\n')
    almost_x86 = compiler.assign_homes(pseudo_x86)
    trace_ast_and_concrete(almost_x86)

    # Skip the patch-pass to have ref to memo in same instr.
    # trace('\n# patch instructions\n')
    # x86 = compiler.patch_instructions(almost_x86)
    # trace_ast_and_concrete(x86)

    # SKIP : Assign_home Pass and Patch_instr Pass
    trace('\n# prelude and conclusion\n')
    x86 = compiler.prelude_and_conclusion(pseudo_x86)
    # x86 = compiler.prelude_and_conclusion(almost_x86)
    # x86 = compiler.prelude_and_conclusion(x86)
    trace_ast_and_concrete(x86)
    # print(x86)

    trace('\n# uncover liveness\n')
    current_instr = x86
    print(current_instr)
    ia_map = compiler.uncover_live(current_instr)
    instrs = current_instr.get_body()
    print_ia_map(instrs, ia_map)

    # Draw inference graph

    # Output x86 program to the .s file
    # x86_filename = program_root + ".s"
    # with open(x86_filename, "w") as dest:
    #     dest.write(str(x86))

    # Given a test file name, the name of a language, a compiler, a type

compile(compiler, "tests/var/register_anal.temp")