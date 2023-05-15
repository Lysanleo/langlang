import os
import compiler
import interp_Lvar
import type_check_Lvar
import interp_Lif
import type_check_Lif
from utils import enable_tracing, run_tests, run_one_test
from interp_x86.eval_x86 import interp_x86

compiler = compiler.Compiler()

# Test Options for Lvar

typecheck_Lvar = type_check_Lvar.TypeCheckLvar().type_check

typecheck_dict = {
    'source': typecheck_Lvar,
    'remove_complex_operands': typecheck_Lvar,
}
interpLvar = interp_Lvar.InterpLvar().interp
interp_dict = {
    'remove_complex_operands': interpLvar,
    'select_instructions': interp_x86,
    'assign_homes': interp_x86,
    'patch_instructions': interp_x86,
}


# Test Options for Lif

typecheckLif = type_check_Lif.TypeCheckLif().type_check
interpLif = interp_Lif.InterpLif().interp

typecheck_if_dict = {
    'source': typecheckLif,
    'shrink': typecheckLif,
    'remove_complex_operands': typecheckLif,
}
interp_if_dict = {
    'shrink': interpLif,
    'remove_complex_operands': interpLif,
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
    run_tests('if', compiler, 'if',
              typecheck_if_dict,
              interp_if_dict)
    run_tests('var', compiler, 'var',
              typecheck_dict,
              interp_dict)

