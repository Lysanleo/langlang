import os
import compiler
import interp_Lif
import type_check_Lif
from utils import run_tests, run_one_test
from interp_x86.eval_x86 import interp_x86

compiler = compiler.Compiler()

typecheck_Lif = type_check_Lif.TypeCheckLif().type_check