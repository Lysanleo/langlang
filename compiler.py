import ast
from ast import *
from utils import *
from x86_ast import *
import x86_ast
# from interp_x86.x86exp import Retq
import os
from typing import List, Tuple, Set, Dict
import math

Binding = Tuple[Name, expr]
Temporaries = List[Binding]

Label = str
Stmts = List[stmt]
BasicBlocks = Dict[Label,Stmts]

class Compiler:
    ############################################################################
    # Shrink if
    ############################################################################

    def shrink_expr(self, e:expr) -> expr:
        # print(e)
        match e:
            case BoolOp(boolop, [e1, e2]):
                match boolop:
                    case And():
                        new_expr = IfExp(e1, e2, Constant(False))
                    case Or():
                        new_expr = IfExp(e1, Constant(True), e2)
                return new_expr
            case IfExp(test, e2, e3):
                new_test = self.shrink_expr(test)
                new_e2 = self.shrink_expr(e2)
                new_e3 = self.shrink_expr(e3)
                return IfExp(new_test, new_e2, new_e3)
            case UnaryOp(op, e):
                new_e = self.shrink_expr(e)
                return UnaryOp(op, new_e)
            case Compare(e1, [cmp], [e2]):
                new_e1 = self.shrink_expr(e1)
                new_e2 = self.shrink_expr(e2)
                return Compare(new_e1, [cmp], [new_e2])
            case BinOp(e1, op, e2):
                new_e1 = self.shrink_expr(e1)
                new_e2 = self.shrink_expr(e2)
                return BinOp(new_e1, op, new_e2)
            case _:
                return e

    def shrink_stmt(self, s:stmt) -> stmt:
        match s:
            case If(exp, s1, s2):
                new_s1 = [self.shrink_stmt(stm) for stm in s1]
                new_s2 = [self.shrink_stmt(stm) for stm in s2]
                return If(self.shrink_expr(exp), new_s1, new_s2)
            case Assign(vars, e):
                return Assign(vars, self.shrink_expr(e))
            case Expr(Call(func, [e])):
                return Expr(Call(func,[self.shrink_expr(e)]))
            case Expr(e):
                return Expr(self.shrink_expr(e))
            case _:
                return s

    def shrink(self, p:Module) -> Module:
        match p:
            case Module(body):
                print(body)
                new_body = [self.shrink_stmt(s) for s in body]
        return Module(new_body)

    ############################################################################
    # Remove Complex Operands
    ############################################################################

    def rco_flat(self, rcolist: Tuple[expr, Temporaries]) -> List[stmt]:
        stmts = [Assign([atmtp[0]], atmtp[1]) for atmtp in rcolist[1]]
        # print(stmts)
        return stmts

    def rco_atom(self, e:expr) -> Tuple[expr, Temporaries]:
        pass

    def rco_exp(self, e: expr, need_atomic: bool) -> Tuple[expr, Temporaries]:
        new_sym = ""
        match e:
            case Constant(value):
                return (e, [])
            case Name(id):
                # return (e, [(e, e)])
                return (e, [])
            case BinOp(latm, Add(), ratm):
                atm1 = self.rco_exp(latm, True)
                atm2 = self.rco_exp(ratm, True)
                new_expr = BinOp(atm1[0], Add(), atm2[0])
                new_bindings = atm1[1] + atm2[1]
                # print("In BinOp Case:")
                # print(new_bindings)
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
            case UnaryOp(Not(), atm):
                atm1 = self.rco_exp(atm, True)
                new_expr = UnaryOp(Not(), atm1[0])
                new_bindings = atm1[1]
                if need_atomic:
                    new_sym = generate_name("tmp")
                    return (Name(new_sym), new_bindings + [(Name(new_sym), new_expr)])
                return (new_expr, new_bindings)
            case Call(Name('input_int'), []):
                new_expr = e
                if need_atomic:
                    new_sym = generate_name("tmp")
                    return (Name(new_sym), [(Name(new_sym), new_expr)])
                return (e, [])
            case Compare(latm, [cmp], [ratm]):
                atm1 = self.rco_exp(latm, True)
                atm2 = self.rco_exp(ratm, True)
                new_expr = Compare(atm1[0], [cmp], [atm2[0]])
                new_bindings = atm1[1] + atm2[1]
                if need_atomic:
                    new_sym = generate_name("tmp")
                    return (Name(new_sym), new_bindings + [(Name(new_sym), new_expr)])
                return (new_expr, new_bindings)
            case IfExp(e1, e2, e3):
                atm1 = self.rco_exp(e1, False)
                ss1 = self.rco_stmt(Expr(e2))
                ss2 = self.rco_stmt(Expr(e3))
                print("ss1:", ss1)
                new_expr = IfExp(atm1[0], Begin(ss1[0:len(ss1)-1], ss1[len(ss1)-1].value),
                                          Begin(ss2[0:len(ss1)-1], ss2[len(ss2)-1].value))
                new_bindings = atm1[1]
                if need_atomic:
                    new_sym = generate_name("tmp")
                    new_bindings = new_bindings + [(Name(new_sym), new_expr)]
                    return (Name(new_sym), new_bindings)
                return (new_expr, new_bindings)

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
                # print(rcotp)
                new_exprs = self.rco_flat(rcotp)
                new_exprs.append(Assign([Name(var)], rcotp[0]))
                # print(new_exprs)
                return new_exprs
            case If(e1, ss1, ss2):
                rcotp = self.rco_exp(e1, False)
                new_exprs = self.rco_flat(rcotp)
                # print(ss1)
                # print(ss2)
                new_ss1_temp = [self.rco_stmt(stm) for stm in ss1]
                new_ss2_temp = [self.rco_stmt(stm) for stm in ss2]
                new_ss1 = []
                new_ss2 = []
                for stmts in new_ss1_temp:
                    if stmts:
                        new_ss1 = new_ss1 + stmts
                for stmts in new_ss2_temp:
                    if stmts:
                        new_ss2 = new_ss2 + stmts
                # print(new_exprs)
                # print(rcotp)
                new_exprs.append(If(rcotp[0], new_ss1, new_ss2))
                return new_exprs

    def remove_complex_operands(self, p: Module) -> Module:
        match p:
            case Module(body):
                # print("here")
                # print(body)
                new_body = []
                new_body_temp = [self.rco_stmt(s) for s in body]
                # print(new_body_temp == [None]) => True
                for stmts in new_body_temp:
                    new_body = new_body + stmts
                print(new_body)
                return Module(new_body)
        
    ############################################################################
    # Explicate Control
    ############################################################################

    def create_block(self, stmts:List[stmt], basic_blocks:Dict[str,List[stmt]]) -> List[stmt]:
        match stmts:
            case [Goto(l)]:
                return stmts
            case _:
                label = label_name(generate_name('block'))
                basic_blocks[label] = stmts
                return [Goto(label)]

    def explicate_effect(self, e:expr, cont:Stmts, basic_blocks:Dict[str,List[stmt]]) -> Stmts:
        match e:
            case IfExp(test, body, orelse):
                cont = self.create_block(cont, basic_blocks)
                br1 = self.explicate_effect(body, cont, basic_blocks)
                br2 = self.explicate_effect(orelse, cont, basic_blocks)
                return self.explicate_pred(test, br1, br2, basic_blocks)
            case Call(func, args):
                # Translate it directly to a Expr AST node(a statement).
                new_cont = [Expr(e)] + cont
                return new_cont
            case Begin(body, result):
                # Begin in $L_if^mon$ only(?) exists in IfExp branches
                ret_stmt = Return(result)
                return body+[ret_stmt]+cont
            case _:
                # No side-effects, discard it
                return cont
                
    
    def explicate_assign(self, rhs, lhs, cont, basic_blocks) -> Stmts:
        match rhs:
            case IfExp(test, body, orelse):
                # Pack the stmt should be excuted after this assign as a block(?)
                # print(lhs, rhs)
                cont = self.create_block(cont, basic_blocks)
                new_body = self.explicate_assign(body, lhs, cont, basic_blocks)
                new_orelse = self.explicate_assign(orelse, lhs, cont, basic_blocks)
                goto_thn = self.create_block(new_body, basic_blocks)
                goto_els = self.create_block(new_orelse, basic_blocks)
                new_cond = self.explicate_pred(test, goto_thn, goto_els, basic_blocks)
                # Clear cont by the way.
                return new_cond
            case Begin(body, result):
                return [Assign([lhs], result)] + (cont if cont else [])
            case _:
                if (cont == None):
                    print(lhs, rhs)
                return [Assign([lhs], rhs)] + (cont if cont else [])

    def explicate_pred(self, cnd:expr, thn, els, basic_blocks) -> Stmts:
        match cnd:
            case Compare(left, [op], [right]):
                return [If(cnd, thn, els)] 
            case Constant(True):
                return thn; 
            case Constant(False):
                return els; 
            case UnaryOp(Not(), operand):
                return [If(operand, els, thn)]
            case IfExp(test, body, orelse):
                goto_then = self.explicate_pred(body.result, thn, els, basic_blocks)
                goto_else = self.explicate_pred(orelse.result, thn, els, basic_blocks)
                goto_body = self.create_block(goto_then, basic_blocks)
                goto_orelse = self.create_block(goto_else, basic_blocks)
                new_test = self.explicate_pred(test, body.body+goto_body, orelse.body+goto_orelse, basic_blocks)
                print("new test:")
                print(new_test)
                # cont = self.create_block(cont, basic_blocks)
                return new_test
            case Begin(body, result):
                return body.append(Expr(result))
            case _:
                return [If(Compare(cnd, [Eq()], [Constant(False)]),
                           self.create_block(els, basic_blocks),
                           self.create_block(thn, basic_blocks))]

    def explicate_stmt(self, s:stmt, cont:Stmts, basic_blocks:BasicBlocks) -> Stmts:
        match s:
            case Assign([lhs], rhs):
                return self.explicate_assign(rhs, lhs, cont, basic_blocks)
            case Expr(value):
                return self.explicate_effect(value, cont, basic_blocks)
            case If(test, body, orelse):
                # Similar to IfExp
                # If(Compare(atm,[cmp],[atm]), [Goto(label)], [Goto(label)])
                goto_body = self.create_block(body, basic_blocks)
                goto_orelse = self.create_block(orelse, basic_blocks)
                return [If(test, goto_body, goto_orelse)]

    def explicate_control(self, p:Module):
        match p:
            case Module(body):
                new_body = [Return(Constant(0))]
                basic_blocks = {}
                for s in reversed(body):
                    new_body = self.explicate_stmt(s, new_body, basic_blocks)
                basic_blocks[label_name('start')] = new_body
                print(basic_blocks)
                return CProgram(basic_blocks)

    ############################################################################
    # Select Instructions
    ############################################################################
    
    regs = ['rsp', 'rbp', 'rax', 'rbx'
           , 'rcx', 'rdx', 'rsi', 'rdi'
           , 'r8', 'r9', 'r10', 'r11'
           , 'r12', 'r13', 'r14', 'r15']

    def select_arg(self, e: expr) -> arg:
        match e:
            case Constant(x) if isinstance(x, bool):
                return Immediate(1 if x else 0)
            case Constant(x) if isinstance(x, int):
                return Immediate(x)
            case Reg(_):
                return e
            case Name(var):
                return Variable(var)
    def cmp_helper(self, cmp) -> str:
        match cmp:
            case Eq():    cc = "e"
            case NotEq(): cc = "ne"
            case Lt():    cc = "l"
            case LtE():   cc = "le"
            case Gt():    cc = "g"
            case GtE():   cc = "ge"
        return cc

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

    def assign_helper(self, target:str, e: expr, Variable) -> List[instr]:
        # Patch, don't know if dangerous
        select_arg = self.select_arg
        instrs:List[instr] = []
        match e:
            # Add-Op
            # var = atm + var
            case ( BinOp(Name(x) as var1, Add(), Constant(y) as atm1)
                 | BinOp(Constant(y) as atm1, Add(), Name(x) as var1) ):
                if x == target:
                    return [Instr('addq', [select_arg(atm1), Variable(x)])]
                # TODO
                instrs = instrs + [Instr('movq', [x86_ast.Variable(x), Variable(target)])]
                instrs = instrs + [Instr('addq', [select_arg(atm1), Variable(target)])]
                return instrs
            # var = atm1 + atm2
            case BinOp(Constant(x) as atm1, Add(), Constant(y) as atm2):
                instrs = instrs + [Instr('movq', [select_arg(atm1), Variable(target)])]
                instrs = instrs + [Instr('addq', [select_arg(atm2), Variable(target)])]
                return instrs
            # var = var1 + var2
            case BinOp(Name(x) as var1, Add(), Name(y) as var2):
                if x == target:
                    return [Instr('addq', [Variable(y), Variable(x)])]
                if y == target:
                    return [Instr('addq', [Variable(x), Variable(y)])]
                instrs = instrs + [Instr('movq', [x86_ast.Variable(x), Variable(target)])]
                instrs = instrs + [Instr('addq', [x86_ast.Variable(y), Variable(target)])]
                return instrs
                
            # Sub-Op 
            # var = var1 - atm1
            # ! This can write in one case and replace with a sub-pattern-match
            case BinOp(Name(x) as var1, Sub(), Constant(y) as atm1):
                if x == target:
                    return [Instr('subq', [select_arg(atm1), Variable(x)])]
                instrs = instrs + [Instr('movq', [x86_ast.Variable(x), Variable(target)])]
                instrs = instrs + [Instr('subq', [select_arg(atm1), Variable(target)])]
                return instrs
            # var = atm1 - var1
            case BinOp(Constant(y) as atm1, Sub(), Name(x) as var1):
                # TODO
                instrs = instrs + [Instr('movq', [select_arg(atm1), Variable(target)])]
                instrs = instrs + [Instr('subq', [Variable(x), Variable(target)])]
                return instrs
            # var = atm1 - atm2
            case BinOp(Constant(x) as atm1, Sub(), Constant(y) as atm2):
                instrs = instrs + [Instr('movq', [select_arg(atm1), Variable(target)])]
                instrs = instrs + [Instr('subq', [select_arg(atm2), Variable(target)])]
                return instrs
            # var = var1 - var2
            case BinOp(Name(x) as var1, Sub(), Name(y) as var2):
                if x == target:
                    return [Instr('subq', [Variable(y), Variable(x)])]
                instrs = instrs + [Instr('movq', [x86_ast.Variable(x), Variable(target)])]
                instrs = instrs + [Instr('subq', [x86_ast.Variable(y), Variable(target)])]
                return instrs

            # var = -var1 
            case UnaryOp(USub(), atm1):
                match atm1:
                    case Constant(_):
                        instrs = instrs + [Instr('movq', [select_arg(atm1)
                                                         , Variable(target)])]
                        instrs = instrs + [Instr('negq', [Variable(target)])]
                        return instrs
                    case Name(var):
                        if var == target:
                            return [Instr('negq', [atm1])]
                        instrs = instrs + [Instr('movq', [select_arg(atm1), Variable(target)])]
                        instrs = instrs + [Instr('negq', [Variable(target)])]
                        return instrs
            # var = not bool_var1
            case UnaryOp(Not(), operand):
                match operand:
                    case Name(var) if var == target:
                        instrs = [Instr('xorq', [Immediate(1), Variable(target)])]
                    case Constant(_) | Name(_):
                        instrs = [Instr('movq', [select_arg(operand), Variable(target)])]
                        # movq arg, var
                        # xorq $1, var
                        instrs += [Instr('xorq', [Immediate(1), Variable(target)])]
                return instrs
            case Compare(operand1, [cmp], operand2):
                cc = self.cmp_helper(cmp)
                instrs = [Instr("cmpq", [operand2, operand1])]
                instrs.append(Instr("set"+cc, [ByteReg('al')]))
                instrs.append(Instr("movzbq", [ByteReg('al'), Variable(target)]))
                return instrs

            # var = Constant 
            case Constant(value) as atm1:
                instrs = instrs + [Instr('movq', [select_arg(atm1), Variable(target)])]
                return instrs
            # var = var
            case Name(var) as atm1:
                instrs = instrs + [Instr('movq', [select_arg(atm1), Variable(target)])]
                return instrs
            case Call(Name('input_int'), []):
                instrs = self.select_instr(e)
                instrs = instrs + [Instr('movq', [select_arg(Reg('rax'))
                                                 , Variable(target)])]
                return instrs

    def select_stmt(self, s: stmt) -> List[instr]:
        # Patch, don't know if dangerous
        select_instr = self.select_instr
        match s:
            # Match call function
            case Expr(Call(Name(funcname), [args]) as expr):
                instrs = select_instr(expr)
                # print(stmt)
                # print(instrs)
            case Expr(expr):
                #TODO
                instrs = select_instr(expr)
                # print(stmt)
                # print(instrs)
            case Assign([Name(var)], expr):
                instrs = self.assign_helper(var, expr, Variable=Variable)
                # print(stmt)
                # print(instrs)
            case Goto(label):
                instrs = [Jump(label)]
            case If(Compare(atm1, [cmp], [atm2]), [Goto(label1)], [Goto(label2)]):
                cc = self.cmp_helper(cmp)
                instrs = [Instr("cmpq", [self.select_arg(atm2), self.select_arg(atm1)])]
                instrs.append(JumpIf(cc, label1))
                instrs.append(Jump(label2))
            case Return(expr):
                #TODO I need to assign exp to %rax, but that would requiring
                # a lot modifies to assign_helper.
                # The reason is that i hard code and assumed every target is a variable.
                instrs = self.assign_helper("rax", expr, Variable=Reg)
                # instrs = self.assign_helper
                instrs.append(Jump("conclusion"))
                #TODO depend on a little conclusion
        return instrs
                

    def select_instructions(self, p: Module | CProgram) -> X86Program:
        match p:
            case Module(body):
                new_body = []
                new_body_temp = [self.select_stmt(stmt) for stmt in body]
                for stmts in new_body_temp:
                    new_body = new_body + stmts
                print("select_instruciton PASS:")
                print(X86Program(new_body))
                # new_body = self.assign_homes_instrs(new_body, {})
                # print("assign_homes PASS:")
                # print(X86Program(new_body))
                # new_body = self.patch_instrs(new_body)
                # print("patch_instructions PASS:")
                # print(X86Program(new_body))
                return X86Program(new_body)
            case CProgram(body):
                new_body = {}
                for (k,v) in body.items():
                    new_body_temp = [self.select_stmt(stmt) for stmt in v]
                    stmts_temp = []
                    for stmts in new_body_temp:
                        stmts_temp += stmts
                    new_body[k] = stmts_temp
                return X86Program(new_body)

    ############################################################################
    # Assign Homes
    ############################################################################

    instrs_two = ['addq', 'subq', 'movq']
    instrs_one = ['negq', 'pushq', 'popq']

    def calculate_offset(self, home: Dict[Variable, arg]) -> int:
        min = 0
        for (_, arg) in home.items():
            match arg:
                case Deref(_, x):
                    if x < min:
                        min = x
        return min-8

    def assign_homes_arg(self, a: arg, home: Dict[Variable, arg]) -> arg:
        match a:
            case Variable(var): # Use Deref(reg, int)
                if var in home:
                    return home[var]
                else:
                    home[var] = Deref('rbp', self.calculate_offset(home))
                    return home[var]
            case _:   # Immediate/Reg
                return a

    def assign_homes_instr(self, i: instr,
                           home: Dict[Variable, arg]) -> instr:
        match i:
            case Instr(cmd, [arg1, arg2]) if cmd in self.instrs_two:
                return Instr(cmd, [self.assign_homes_arg(arg1, home), self.assign_homes_arg(arg2, home)])
            case Instr(cmd, [arg1]) if cmd in self.instrs_one:
                return Instr(cmd, [self.assign_homes_arg(arg1, home)])
            case _:
                return i

    def assign_homes_instrs(self, ss: List[instr],
                            home: Dict[Variable, arg]) -> List[instr]:
        ss = [self.assign_homes_instr(i, home) for i in ss]
        return ss

    def assign_homes(self, p: X86Program) -> X86Program:
        home = {}
        match p:
            case X86Program(body):
                new_body = self.assign_homes_instrs(body, home)
                x86prog = X86Program(new_body)
                stack_space = math.ceil(abs(self.calculate_offset(home)) / 16) * 16
                print(stack_space)
                x86prog.stack_space = stack_space
                x86prog.home = home
                return x86prog

    ############################################################################
    # Patch Instructions
    ############################################################################

    def patch_instr(self, i: instr) -> List[instr]:
        instrs = []
        match i:
            case Instr(cmd, [arg1, arg2]) if cmd in self.instrs_two:
                match (arg1, arg2):
                    case (Deref(_) as d1, Deref(_) as d2) if d1 == d2 and cmd == 'movq':
                        instrs.append(i)
                    case (Deref(_) as d1, Deref(_) as d2):
                        instrs.append(Instr('movq', [arg1, Reg('rax')]))
                        instrs.append(Instr(cmd, [Reg('rax'), arg2]))
                    case (Immediate(x), _):
                        if (x > 2**16):
                            instrs.append(Instr('movq', [arg1, Reg('rax')]))
                            instrs.append(Instr(cmd, [Reg('rax'), arg2]))
                        else:
                            instrs.append(i)
                    case _:
                        instrs.append(i)
                return instrs
            case Instr(cmd, [arg1]) if cmd in self.instrs_one:
                match arg1:
                    case Immediate(x):
                        if (x > 2**16):
                            instrs.append(Instr('movq', [arg1, Reg('rax')]))
                            instrs.append(Instr(cmd, [Reg('rax')]))
                        else:
                            instrs.append(i)
                    case _:
                        instrs.append(i)
                return instrs
            case _:
                return [i]
                
                        

    def patch_instrs(self, ss: List[instr]) -> List[instr]:
        ss = [self.patch_instr(i) for i in ss]
        # print(ss)
        ss = [i for ins in ss for i in ins]
        return ss

    def patch_instructions(self, p: X86Program) -> X86Program:
        match p:
            case X86Program(body):
                new_body = self.patch_instrs(body)
                x86prog = X86Program(new_body)
                x86prog.stack_space = p.stack_space
                x86prog.home = p.home
                return x86prog

    ############################################################################
    # Prelude & Conclusion
    ############################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        match p:
            case X86Program(body):
                new_body = body
                # Prelude
                new_body = [Instr('pushq', [Reg('rbp')])
                           , Instr('movq', [Reg('rsp'), Reg('rbp')])
                           , Instr('subq', [Immediate(p.stack_space), Reg('rsp')])] + new_body
                # Conclusion
                new_body.append(Instr('addq', [Immediate(p.stack_space), Reg('rsp')]))
                new_body.append(Instr('popq', [Reg('rbp')]))
                new_body.append(Retq())
                x86prog = X86Program({'main':new_body})
                x86prog.stack_space = p.stack_space
                x86prog.home = p.home
                return x86prog

