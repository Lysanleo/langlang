import ast
from ast import *
from utils import *
from x86_ast import *
import os
from typing import List, Tuple, Set, Dict

Binding = Tuple[Name, expr]
Temporaries = List[Binding]


class Compiler:

    ############################################################################
    # Remove Complex Operands
    ############################################################################

    def rco_flat(self, rcolist: Tuple[expr, Temporaries]) -> List[stmt]:
        stmts = [Assign([atmtp[0]], atmtp[1]) for atmtp in rcolist[1]]
        print(stmts)
        return stmts

    def rco_exp(self, e: expr, need_atomic: bool) -> Tuple[expr, Temporaries]:
        new_sym = ""
        match e:
            case Constant(value):
                return (e, [])
            case Name(id):
                return (e, [(e, e)])
            case BinOp(latm, Add(), ratm):
                atm1 = self.rco_exp(latm, True)
                atm2 = self.rco_exp(ratm, True)
                new_expr = BinOp(atm1[0], Add(), atm2[0])
                new_bindings = atm1[1] + atm2[1]
                print(new_bindings)
                if need_atomic:
                    new_sym = generate_name("tmp")
                    return (Name(new_sym), new_bindings + [(Name(new_sym), new_expr)])
                return (new_expr, new_bindings)
            case BinOp(latm, Sub(), ratm):
                atm1 = self.rco_exp(latm, True)
                atm2 = self.rco_exp(ratm, True)
                new_expr = BinOp(atm1[0], Sub(), atm2[0])
                new_bindings = atm1[1] + atm2[1]
                if need_atomic:
                    new_sym = generate_name("tmp")
                    return (Name(new_sym), new_bindings + [([Name(new_sym)], new_expr)])
                return (new_expr, new_bindings)
            case UnaryOp(USub(), atm):
                atm1 = self.rco_exp(atm, True)
                new_expr = UnaryOp(USub(), atm1[0])
                new_bindings = atm1[1]
                if need_atomic:
                    new_sym = generate_name("tmp")
                    return (Name(new_sym), new_bindings + [(Name(new_sym), new_expr)])
                return (new_expr, new_bindings)
            case Call(Name('input_int'), []):
                return (e, [])

    def rco_stmt(self, s: stmt) -> List[stmt]:
        match s:
            case Expr(Call(Name('print'), [atom])):
                # print(atom)
                rcotp = self.rco_exp(atom, True)
                # print(rcotp)
                new_exprs = self.rco_flat(rcotp)
                new_exprs.append(Expr(Call(Name('print'), [rcotp[0]])))
                # print(new_exprs)
                return new_exprs
            case Expr(exp):
                rcotp = self.rco_exp(exp, False)
                new_exprs = self.rco_flat(rcotp)
                new_exprs.append(Expr(rcotp[0]))
                return new_exprs
            case Assign([Name(var)], exp):
                rcotp = self.rco_exp(exp, False)
                new_exprs = self.rco_flat(rcotp)
                new_exprs.append(Assign([Name(var)], rcotp[0]))
                return new_exprs

    def remove_complex_operands(self, p: Module) -> Module:
        match p:
            case Module(body):
                print(body)
                new_body = []
                new_body_temp = [self.rco_stmt(s) for s in body]
                # print(new_body_temp == [None]) => True
                for stmts in new_body_temp:
                    new_body = new_body + stmts
                print(new_body)
                return Module(new_body)
        

    ############################################################################
    # Select Instructions
    ############################################################################
    
    regs = ['rsp', 'rbp', 'rax', 'rbx'
           , 'rcx', 'rdx', 'rsi', 'rdi'
           , 'r8', 'r9', 'r10', 'r11'
           , 'r12', 'r13', 'r14', 'r15']

    def select_arg(self, e: expr) -> arg:
        match e:
            case Constant(x):
                return Immediate(x)
            case Reg(_):
                return e

    def select_instr(self, e: expr) -> List[instr]:
        # Patch, don't know if dangerous
        select_arg = self.select_arg
        instrs:List[instr] = []
        match e:
            case Call(Name('print'), [atm]):
                instrs.append(Instr('movq', [select_arg(atm), select_arg(Reg('rdi'))]))
                instrs.append(Callq('print_int', 1))
                return instrs
            case Call(Name('input_int'), []):
                instrs.append(Callq('read_int', 0))
                return instrs

    def assign_helper(self, target:str, e: expr) -> List[instr]:
        # Patch, don't know if dangerous
        select_arg = self.select_arg
        instrs:List[instr] = []
        match e:
            # Add-Op
            # var = atm + var
            case ( BinOp(Name(x) as var1, Add(), Constant(y) as atm1)
                 | BinOp(Constant(y) as atm1, Add(), Name(x) as var1) ):
                if x == target:
                    return [Instr('addq', [select_arg(atm1), var1])]
                # TODO
                instrs = instrs + [Instr('movq', [var1, Name(target)])]
                instrs = instrs + [Instr('addq', [select_arg(atm1), Name(target)])]
                return instrs
            # var = atm1 + atm2
            case BinOp(Constant(x) as atm1, Add(), Constant(y) as atm2):
                instrs = instrs + [Instr('movq', [select_arg(atm1), Name(target)])]
                instrs = instrs + [Instr('addq', [select_arg(atm2), Name(target)])]
                return instrs
            # var = var1 + var2
            case BinOp(Name(x) as var1, Add(), Name(y) as var2):
                if x == target:
                    return [Instr('addq', [var2, var1])]
                if y == target:
                    return [Instr('addq', [var1, var2])]
                instrs = instrs + [Instr('movq', [var1, Name(target)])]
                instrs = instrs + [Instr('addq', [var2, Name(target)])]
                return instrs
                
            # Sub-Op 
            # var = var1 - atm1
            # ! This can write in one case and replace with a sub-pattern-match
            case BinOp(Name(x) as var1, Sub(), Constant(y) as atm1):
                if x == target:
                    return [Instr('subq', [select_arg(atm1), var1])]
                instrs = instrs + [Instr('movq', [var1, Name(target)])]
                instrs = instrs + [Instr('subq', [select_arg(atm1), Name(target)])]
                return instrs
            # var = atm1 - var1
            case BinOp(Constant(y) as atm1, Sub(), Name(x) as var1):
                # TODO
                instrs = instrs + [Instr('movq', [select_arg(atm1), Name(target)])]
                instrs = instrs + [Instr('subq', [var1, Name(target)])]
                return instrs
            # var = atm1 - atm2
            case BinOp(Constant(x) as atm1, Sub(), Constant(y) as atm2):
                instrs = instrs + [Instr('movq', [select_arg(atm1), Name(target)])]
                instrs = instrs + [Instr('subq', [select_arg(atm2), Name(target)])]
                return instrs
            # var = var1 - var2
            case BinOp(Name(x) as var1, Sub(), Name(y) as var2):
                if x == target:
                    return [Instr('subq', [var2, var1])]
                instrs = instrs + [Instr('movq', [var1, Name(target)])]
                instrs = instrs + [Instr('subq', [var2, Name(target)])]
                return instrs

            # Neg-Op
            case UnaryOp(USub(), atm1):
                match atm1:
                    case Constant(_):
                        instrs = instrs + [Instr('movq', [select_arg(atm1)
                                                         , Name(target)])]
                        instrs = instrs + [Instr('negq', [Name(target)])]
                        return instrs
                    case Name(var):
                        if var == target:
                            return [Instr('negq', [atm1])]
                        instrs = instrs + [Instr('movq', [atm1, Name(target)])]
                        instrs = instrs + [Instr('negq', [Name(target)])]
                        return instrs
            # var = Constant 
            case Constant(value) as atm1:
                instrs = instrs + [Instr('movq', [select_arg(atm1), Name(target)])]
                return instrs
            # var = var
            case Name(var) as atm1:
                instrs = instrs + [Instr('movq', [atm1, Name(target)])]
                return instrs
            case Call(Name('input_int'), []):
                instrs = self.select_instr(e)
                instrs = instrs + [Instr('movq', [select_arg(Reg('rax'))
                                                 , Name(target)])]
                return instrs

    def select_stmt(self, s: stmt) -> List[instr]:
        # Patch, don't know if dangerous
        select_instr = self.select_instr
        match s:
            # Match call function
            case Expr(Call(Name(funcname), [args]) as expr):
                return select_instr(expr)
            case Expr(expr):
                #TODO
                return select_instr(expr)
            case Assign([Name(var)], expr):
                return self.assign_helper(var, expr)
                

    def select_instructions(self, p: Module) -> X86Program:
        match p:
            case Module(body):
                new_body = []
                new_body_temp = [self.select_stmt(stmt) for stmt in body]
                for stmts in new_body_temp:
                    new_body = new_body + stmts
                print(new_body)
                return X86Program(new_body)

    ############################################################################
    # Assign Homes
    ############################################################################

    def assign_homes_arg(self, a: arg, home: Dict[Variable, arg]) -> arg:
        # YOUR CODE HERE
        pass        

    def assign_homes_instr(self, i: instr,
                           home: Dict[Variable, arg]) -> instr:
        # YOUR CODE HERE
        pass        

    def assign_homes(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        pass        

    ############################################################################
    # Patch Instructions
    ############################################################################

    def patch_instr(self, i: instr) -> List[instr]:
        # YOUR CODE HERE
        pass        

    def patch_instructions(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        pass        

    ############################################################################
    # Prelude & Conclusion
    ############################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        pass        

