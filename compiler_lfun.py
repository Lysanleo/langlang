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
    
    def reveal_exp_functions(self, exp:expr, func_param_n_map:dict) -> expr:
        match exp:
            case Constant(_):
                return exp

            case Call(Name('input_int'), []):
                return exp

            case Call(Name(funcname), [arg_exp]) if funcname in ["print", "len"]:
                return Call(Name(funcname), [self.reveal_exp_functions(arg_exp, func_param_n_map)])

            case UnaryOp(op, operand_exp):
                return UnaryOp(op, self.reveal_exp_functions(operand_exp, func_param_n_map))

            case BinOp(left_exp, op, right_exp):
                new_left_exp = self.reveal_exp_functions(left_exp, func_param_n_map)
                new_right_exp = self.reveal_exp_functions(right_exp, func_param_n_map)
                return BinOp(new_left_exp, op, new_right_exp)

            case BoolOp(bop, [e1, e2]):
                new_e1 = self.reveal_exp_functions(e1, func_param_n_map)
                new_e2 = self.reveal_exp_functions(e2, func_param_n_map)
                return BoolOp(bop, [new_e1, new_e2])
                
            case Call(func, args):
                f = self.reveal_exp_functions(func, func_param_n_map)
                new_args = [self.reveal_exp_functions(arg, func_param_n_map) for arg in args]
                return Call(f, new_args)

            case Compare(e1, [cmp], e2):
                new_e1 = self.reveal_exp_functions(e1, func_param_n_map)
                new_e2 = self.reveal_exp_functions(e2, func_param_n_map)
                return Compare(new_e1, [cmp], new_e2)
            
            case IfExp(test_e, body_e, orelse_e):
                new_test_e = self.reveal_exp_functions(test_e, func_param_n_map)
                new_body_e = self.reveal_exp_functions(body_e, func_param_n_map)
                new_orelse_e = self.reveal_exp_functions(orelse_e, func_param_n_map)
                return IfExp(new_test_e, new_body_e, new_orelse_e)

            case Subscript(e, Constant(int), Load()):
                new_e = self.reveal_exp_functions(e, func_param_n_map)
                return Subscript(new_e, Constant(int), Load())

            case Tuple(es, Load()):
                new_es = [self.reveal_exp_functions(e, func_param_n_map) for e in es]
                return Tuple(new_es, Load())
            
            case Name(name) if name in func_param_n_map.keys():
                return FunRef(name, func_param_n_map[name])
            
            case _:
                raise Exception('compiler_lfun reveal_exp_functions: unexpected ' + repr(exp))

    def reveal_stmt_functions(self, stm:stmt, func_param_n_map:dict) -> stmt:
        match stm:
            case Expr(exp):
                pass
            case Assign(target, exp):
                pass
            case If(test, body_stmt, orelse_stmt):
                pass
            case While(test, body_stmt, orelse_stmt):
                pass
            case Return(exp):
                pass

    def replace_func_refs(self, p:FunctionDef, func_param_n_map:dict) -> FunctionDef:
        match p:
            case FunctionDef(name, args, body, _, ret_type, _):
                # use list comprehension to iterate on the body
                new_body = [self.reveal_stmt_functions(s, func_param_n_map) for s in body]
                return FunctionDef(name, args, new_body, None, ret_type, None)

    # create a new pass named reveal_functions that changes function references from Name(f ) to FunRef(f , n) where n is the arity of the function
    def reveal_functions(self, p:Module) -> Module:
        match p:
            case Module(body):
                func_param_n_map = {}
                # user defined function map
                for s in body:
                    if isinstance(s, FunctionDef):
                        func_param_n_map[s.name] = len(s.args)
                new_body = [self.replace_func_refs(fundef, func_param_n_map) for fundef in body if isinstance(fundef, FunctionDef)]
                return new_body


    def limit_functions(self, p:Module) -> Module:
        match p:
            case Module(body):
               pass 

    def remove_complex_operands(self, p:Module) -> Module:
        pass

