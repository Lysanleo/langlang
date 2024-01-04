import compiler_ltup
import pprint
from itertools import filterfalse
from ast import *
from utils import *

pp = pprint.PrettyPrinter()

class CompilerLfun(compiler_ltup.CompilerLtup):
    def shrink(self, p:Module) -> Module:
        # pp.pprint(p)
        # print("\n")
        match p:
            # Module([def ... stmt ...])
            case Module(body):
                mainstmts = []
                defstmts = []
                for s in body:
                    if isinstance(s, FunctionDef):
                        defstmts.append(s)
                    else:
                        mainstmts.append(s)
                new_body = defstmts + [FunctionDef('main', [], mainstmts+[Return(Constant(0))], None, IntType(),None)]
        return Module(new_body)

    def replace_func_refs(self, p:FunctionDef, func_param_n_map:dict) -> FunctionDef:
        match p:
            case FunctionDef(name, args, body, _, ret_type, _):
                new_body = []
                for s in body:
                    #TODO
                    pass
                return FunctionDef(name, args, new_body, None, ret_type, None)

    # create a new pass named reveal_functions that changes function references from Name(f ) to FunRef(f , n) where n is the arity of the function
    def reveal_functions(self, p:Module) -> Module:
        match p:
            case Module(body):
                func_param_n_map = {}
                for s in body:
                    if isinstance(s, FunctionDef):
                        func_param_n_map[s.name] = len(s.args)
                new_body = []
                for fundef in body:
                    new_stmts = []
                    new_stmts.append(replace_func_refs(fundef, func_param_n_map))


    def limit_functions(self, p:Module) -> Module:
        match p:
            case Module(body):
               pass 

    def remove_complex_operands(self, p:Module) -> Module:
        pass

