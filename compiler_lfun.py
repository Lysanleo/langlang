import compiler_ltup
import pprint
from itertools import filterfalse
from ast import *
from data_type import Temporaries
from utils import *

pp = pprint.PrettyPrinter()

class CompilerLfun(compiler_ltup.CompilerLtup):

    ############################################################################
    # Shrink Functions
    ############################################################################
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
    
    ############################################################################
    # Reveal Functions
    ############################################################################

    def reveal_exp_functions(self, exp:expr, func_param_n_map:dict) -> expr:
        match exp:
            case Constant(_):
                return exp

            case Call(Name('input_int'), []):
                return exp

            # built-in function, thus not rewrite to FunRef
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

            case Name(name):
                return Name(name)
            
            case _:
                raise Exception('compiler_lfun reveal_exp_functions: unexpected ' + repr(exp))

    def reveal_stmt_functions(self, stm:stmt, func_param_n_map:dict) -> stmt:
        match stm:
            case Expr(exp):
                new_exp = self.reveal_exp_functions(exp, func_param_n_map)
                return Expr(new_exp)

            case Expr(Call(Name('print'),[exp])):
                new_exp = self.reveal_exp_functions(exp, func_param_n_map)
                return Expr(Call(Name('print'),[new_exp]))

            case Assign([Name(var)] as v, exp):
                new_exp = self.reveal_exp_functions(exp, func_param_n_map)
                return Assign(v, exp)

            case If(test_exp, body_stmts, orelse_stmts):
                new_test_exp = self.reveal_exp_functions(test_exp, func_param_n_map)
                new_body_stmts = [self.reveal_stmt_functions(s, func_param_n_map) for s in body_stmts]
                new_orelse_stmts = [self.reveal_stmt_functions(s, func_param_n_map) for s in orelse_stmts]
                return If(new_test_exp, new_body_stmts, new_orelse_stmts)
                
            case While(test_exp, body_stmts, orelse_stmts):
                new_test_exp = self.reveal_exp_functions(test_exp, func_param_n_map)
                new_body_stmts = [self.reveal_stmt_functions(s, func_param_n_map) for s in body_stmts]
                new_orelse_stmts = [self.reveal_stmt_functions(s, func_param_n_map) for s in orelse_stmts]
                return While(new_test_exp, new_body_stmts, new_orelse_stmts)
            case Return(exp):
                new_exp = self.reveal_exp_functions(exp, func_param_n_map)
                return Return(new_exp)
            
            case _:
                raise Exception('compiler_lfun reveal_stmt_functions: unexpected ' + repr(stm))

    def replace_func_refs(self, p:FunctionDef, func_param_n_map:dict) -> FunctionDef:
        match p:
            case FunctionDef(name, args, body, _, ret_type, _):
                # add new func_param_n info according to args
                # iterate on args, match the FunctionType and get the number of parameters, temporaly add this map to func_param_n_map
                new_func_param_n_map = func_param_n_map.copy()
                for (arg_name, arg_type) in args:
                    # print(args)
                    if isinstance(arg_type, FunctionType):
                        # print(arg_name, arg_type)
                        # print(type(arg_name), type(arg_type))
                        new_func_param_n_map[arg_name] = len(arg_type.param_types)
                # use list comprehension to iterate on the body
                new_body = [self.reveal_stmt_functions(s, new_func_param_n_map) for s in body]
                return FunctionDef(name, args, new_body, None, ret_type, None)
            case _:
                raise Exception('compiler_lfun replace_func_refs: unexpected ' + repr(p))
    
    func_param_n_map = {}
    # create a new pass named reveal_functions that changes function references from Name(f ) to FunRef(f , n) where n is the arity of the function
    def reveal_functions(self, p:Module) -> Module:
        match p:
            case Module(body):
                # @semantic : func and its parameters number
                # user defined function map
                for s in body:
                    if isinstance(s, FunctionDef):
                        # if key is in the map, raise an error
                        if s.name in self.func_param_n_map.keys():
                            raise Exception(f"Function {s.name} is already defined.")
                        self.func_param_n_map[s.name] = len(s.args)
                new_body = [self.replace_func_refs(fundef, self.func_param_n_map) for fundef in body if isinstance(fundef, FunctionDef)]
                return Module(new_body)

    ############################################################################
    # limit functions
    ############################################################################

    def limit_functions_rewrite_exp(self, exp: expr, arg_idx: list[tuple[Name,int]]) -> expr:
        match exp:
            case Constant(_):
                return exp

            case Call(Name('input_int'), []):
                return exp

            # built-in function, thus not rewrite to FunRef
            case Call(Name(funcname), [arg_exp]) if funcname in ["print", "len"]:
                return Call(Name(funcname), [self.limit_functions_rewrite_exp(arg_exp, arg_idx)])

            case UnaryOp(op, operand_exp):
                return UnaryOp(op, self.limit_functions_rewrite_exp(operand_exp, arg_idx))

            case BinOp(left_exp, op, right_exp):
                new_left_exp = self.limit_functions_rewrite_exp(left_exp, arg_idx)
                new_right_exp = self.limit_functions_rewrite_exp(right_exp, arg_idx)
                return BinOp(new_left_exp, op, new_right_exp)

            case BoolOp(bop, [e1, e2]):
                new_e1 = self.limit_functions_rewrite_exp(e1, arg_idx)
                new_e2 = self.limit_functions_rewrite_exp(e2, arg_idx)
                return BoolOp(bop, [new_e1, new_e2])
                
            case Call(func, args):
                f = self.limit_functions_rewrite_exp(func, arg_idx)
                rewrited_args = [self.limit_functions_rewrite_exp(arg, arg_idx) for arg in args]
                new_args = rewrited_args[:5]
                lefted_args = Tuple(rewrited_args[5:], Load())
                new_args.append(lefted_args)
                return Call(f, new_args)

            case Compare(e1, [cmp], e2):
                new_e1 = self.limit_functions_rewrite_exp(e1, arg_idx)
                new_e2 = self.limit_functions_rewrite_exp(e2, arg_idx)
                return Compare(new_e1, [cmp], new_e2)
            
            case IfExp(test_e, body_e, orelse_e):
                new_test_e = self.limit_functions_rewrite_exp(test_e, arg_idx)
                new_body_e = self.limit_functions_rewrite_exp(body_e, arg_idx)
                new_orelse_e = self.limit_functions_rewrite_exp(orelse_e, arg_idx)
                return IfExp(new_test_e, new_body_e, new_orelse_e)

            case Subscript(e, Constant(int), Load()):
                new_e = self.limit_functions_rewrite_exp(e, arg_idx)
                return Subscript(new_e, Constant(int), Load())

            case Tuple(es, Load()):
                new_es = [self.limit_functions_rewrite_exp(e, arg_idx) for e in es]
                return Tuple(new_es, Load())
            
            case Name(name):
                # if name in arg_idx, then Name(x_i) ⇒ Subscript(tup, Constant(k), Load())
                print(arg_idx)
                for (n, i) in arg_idx:
                    if n == name:
                        return Subscript(Name('tup'), Constant(i), Load())
                return Name(name)
            
            case _:
                raise Exception('compiler_lfun limit_functions_rewrite_exp: unexpected ' + repr(exp))
                
    def limit_functions_rewrite_stmt(self, stm:stmt, args_idx:list[tuple[Name,int]]) -> stmt:
        match stm:
            case Expr(exp):
                new_exp = self.limit_functions_rewrite_exp(exp, args_idx)
                return Expr(new_exp)

            case Expr(Call(Name('print'),[exp])):
                new_exp = self.limit_functions_rewrite_exp(exp, args_idx)
                return Expr(Call(Name('print'),[new_exp]))

            case Assign([Name(var)] as v, exp):
                new_exp = self.limit_functions_rewrite_exp(exp, args_idx)
                return Assign(v, exp)

            case If(test_exp, body_stmts, orelse_stmts):
                new_test_exp = self.limit_functions_rewrite_exp(test_exp, args_idx)
                new_body_stmts = [self.reveal_stmt_functions(s, args_idx) for s in body_stmts]
                new_orelse_stmts = [self.reveal_stmt_functions(s, args_idx) for s in orelse_stmts]
                return If(new_test_exp, new_body_stmts, new_orelse_stmts)
                
            case While(test_exp, body_stmts, orelse_stmts):
                new_test_exp = self.limit_functions_rewrite_exp(test_exp, args_idx)
                new_body_stmts = [self.reveal_stmt_functions(s, args_idx) for s in body_stmts]
                new_orelse_stmts = [self.reveal_stmt_functions(s, args_idx) for s in orelse_stmts]
                return While(new_test_exp, new_body_stmts, new_orelse_stmts)

            case Return(exp):
                new_exp = self.limit_functions_rewrite_exp(exp, args_idx)
                return Return(new_exp)
            
            case _:
                raise Exception('compiler_lfun limit_functions_rewrite_stmt: unexpected ' + repr(stm))

    # @semantic: FunctionDef(name, args, body, _, ret_type, _)
    #           -> FunctionDef(name, args', body', _, ret_type, _)
    #           where body->body' and ret_type->ret_type'
    def limit_functions_rewrite_body(self, funcdef:FunctionDef) -> Module:
        match funcdef:
            case FunctionDef(name, args, body, a, ret_type, b):
                # new body of transformed statements
                new_body:list[stmt] = []

                # concat the 0-5 arguments and make the left a tuple
                new_args:list[str, Type] = args[:5]

                # construct a tuple of type TupleType(([T6, ..., Tn]))
                new_tup_type = TupleType([t for (n, t) in args[5:]])
                # TODO dont know if *var* is str or Name
                new_tup_var = generate_name("tup")
                left_tup:tuple[str, Type] = tuple([new_tup_var, new_tup_type])
                new_args.append(left_tup)

                # args and idx in tup
                args_idx_tup = [(n, i) for i, (n, _) in enumerate(args[5:])]

                for s in body:
                    new_s = self.limit_functions_rewrite_stmt(s, args_idx_tup)
                    new_body.append(new_s)
                    
                return FunctionDef(name, new_args, new_body, a, ret_type, b)
                
            case _:
                raise Exception('compiler_lfun limit_functions_rewrite_body: unexpected ' + repr(funcdef))

    def limit_functions(self, p:Module) -> Module:
        match p:
            case Module(body):
                new_body = []
                for func in body:
                    if self.func_param_n_map[func.name] > 6:
                        new_body.append(self.limit_functions_rewrite_body(func))
                    else:
                        new_body.append(func)
                return Module(new_body)

    ############################################################################
    # Expose Allocation
    ############################################################################

    def expose_allocation_rewrite_expr(self, e: expr) -> expr:
        match e:
            case FunRef(label, arity):
                return e
            case Call(func, args):
                new_func = self.expose_allocation_rewrite_expr(func)
                new_args = [self.expose_allocation_rewrite_expr(arg) for arg in args]
                return Call(new_func, new_args)
            case _:
                return super().expose_allocation_rewrite_expr(e)

    def expose_allocation_rewrite_stmt(self, s:stmt) -> stmt:
        match s:
            case Return(exp):
                # print(f"expose_allocation_rewrite_stmt: {exp}")
                new_exp = self.expose_allocation_rewrite_expr(exp)
                return Return(new_exp)
            case _:
                return super().expose_allocation_rewrite_stmt(s)

    def expose_allocation_rewrite_body(self, p:FunctionDef) -> FunctionDef:
        match p:
            case FunctionDef(name, args, body, a, ret_type, b):
                new_body = []
                for stmt in body:
                    new_stmt = self.expose_allocation_rewrite_stmt(stmt)
                    new_body.append(new_stmt)
                return FunctionDef(name, args, new_body, a, ret_type, b)
            case _:
                raise Exception('compiler_lfun expose_allocation_rewrite_body: unexpected ' + repr(p))

    # TODO Correctly handle the tuple creation
    def expose_allocation(self, p: Module) -> Module:
        match p:
            case Module(defs):
                new_defs = []
                for fundef in defs:
                    new_fundef = self.expose_allocation_rewrite_body(fundef)
                    new_defs.append(new_fundef)
                return Module(new_defs)

    def remove_complex_operands(self, p:Module) -> Module:
        pass

