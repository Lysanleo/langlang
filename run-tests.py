import os
import sys

sys.path.append('../python-student-support-code')
sys.path.append('../python-student-support-code/interp_x86')

import compiler
import compiler_register_allocator
import compiler_ltup
import interp_Lvar
import interp_Lif
import interp_Lwhile
import interp_Ltup
import interp_Cif
import interp_Ctup
import type_check_Lvar
import type_check_Lif
import type_check_Lwhile
import type_check_Ltup
import type_check_Cif
import type_check_Ctup
from utils import enable_tracing, run_tests, run_one_test
from interp_x86.eval_x86 import interp_x86


compiler = compiler.Compiler()
compiler_ra = compiler_register_allocator.Compiler()
compiler_ltup = compiler_ltup.CompilerLtup()

# Test Options for Lvar

typecheck_Lvar = type_check_Lvar.TypeCheckLvar().type_check

typecheck_dict = {
    'source': typecheck_Lvar,
    'shrink': typecheck_Lvar,
    'remove_complex_operands': typecheck_Lvar
}
interpLvar = interp_Lvar.InterpLvar().interp
interp_dict = {
    'remove_complex_operands': interpLvar,
    'shrink': interpLvar,
    'select_instructions': interp_x86,
    'assign_homes': interp_x86,
    'patch_instructions': interp_x86,
}


# Test Options for Lif

typecheckLif = type_check_Lif.TypeCheckLif().type_check
typecheckCif = type_check_Cif.TypeCheckCif().type_check
interpLif = interp_Lif.InterpLif().interp
interpCif = interp_Cif.InterpCif().interp

typecheck_if_dict = {
    'source': typecheckLif,
    'shrink': typecheckLif,
    'remove_complex_operands': typecheckLif,
    'explicate_control': typecheckCif
}
interp_if_dict = {
    'shrink': interpLif,
    'remove_complex_operands': interpLif,
    'explicate_control': interpCif,
    'select_instructions': interp_x86,
    'assign_homes': interp_x86,
    'patch_instructions': interp_x86,
}

# Test Options for Lwhile

typecheckLwhile = type_check_Lwhile.TypeCheckLwhile().type_check
typecheckCwhile = typecheckCif
interpLwhile = interp_Lwhile.InterpLwhile().interp
interpCwhile = interpCif

typecheck_while_dict = {
    'source': typecheckLwhile,
    'shrink': typecheckLwhile,
    'remove_complex_operands': typecheckLwhile,
    'explicate_control': typecheckCwhile
}
interp_while_dict = {
    'shrink': interpLwhile,
    'remove_complex_operands': interpLwhile,
    'explicate_control': interpCwhile,
    'select_instructions': interp_x86,
    'assign_homes': interp_x86,
    'patch_instructions': interp_x86,
}

# Test options for Ltup

typecheckLtup = type_check_Ltup.TypeCheckLtup().type_check
typecheckCtup = type_check_Ctup.TypeCheckCtup().type_check
interpLtup = interp_Ltup.InterpLtup().interp
interpCtup = interp_Ctup.InterpCtup().interp

typecheck_tuple_dict = {
    'source': typecheckLtup,
    'expose_allocation': typecheckLtup,
    'remove_complex_operands': typecheckLtup,
    'explicate_control': typecheckCtup
}

interp_tuple_dict = {
    'expose_allocation': interpLtup,
    'remove_complex_operands': interpLtup,
    'explicate_control': interpCtup,
    # 'assign_homes': interp_x86,
    # 'select_instructions': interp_x86,
    'prelude_and_conclusion': interp_x86
}

if False:
    run_one_test(os.getcwd() + '/tests/var/zero.py',
                 'var',
                 compiler,
                 'var',
                 typecheck_dict,
                 interp_dict)
else:
    enable_tracing()
    # run_tests('if', compiler_ra, 'if',
            #   typecheck_if_dict,
            #   interp_if_dict)
    # run_tests('var', compiler_ra, 'var',
            #   typecheck_dict,
            #   interp_dict
    # run_tests('while', compiler_ra, 'while',
            #   typecheck_while_dict,
            #   interp_while_dict)
    run_tests('tuple', compiler_ltup, 'tuple',
              typecheck_tuple_dict,
              interp_tuple_dict)

