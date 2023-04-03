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

    def select_arg(self, e: expr) -> arg:
        # YOUR CODE HERE
        pass        

    def select_stmt(self, s: stmt) -> List[instr]:
        # YOUR CODE HERE
        pass        

    # def select_instructions(self, p: Module) -> X86Program:
    #     # YOUR CODE HERE
    #     pass        

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

    def assign_homes_instrs(self, ss: List[instr],
                            home: Dict[Variable, arg]) -> List[instr]:
        # YOUR CODE HERE
        pass        

    # def assign_homes(self, p: X86Program) -> X86Program:
    #     # YOUR CODE HERE
    #     pass        

    ############################################################################
    # Patch Instructions
    ############################################################################

    def patch_instr(self, i: instr) -> List[instr]:
        # YOUR CODE HERE
        pass        

    def patch_instrs(self, ss: List[instr]) -> List[instr]:
        # YOUR CODE HERE
        pass        

    # def patch_instructions(self, p: X86Program) -> X86Program:
    #     # YOUR CODE HERE
    #     pass        

    ############################################################################
    # Prelude & Conclusion
    ############################################################################

    # def prelude_and_conclusion(self, p: X86Program) -> X86Program:
    #     # YOUR CODE HERE
    #     pass        

