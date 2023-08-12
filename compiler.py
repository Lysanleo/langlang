from ast import *
from utils import *
from x86_ast import *
import x86_ast
# from interp_x86.x86exp import Retq
import os
from typing import List, Set, Dict
import math
from data_type import *

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
            case IfExp(cond_exp, e2, e3):
                new_test = self.shrink_expr(cond_exp)
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
                # print(body)
                new_body = [self.shrink_stmt(s) for s in body]
        return Module(new_body)

    ############################################################################
    # Remove Complex Operands
    ############################################################################

    def build_atomic_pair(
        self,
        atomic_p:bool,
        exp:expr,
        bindings:Temporaries
    ) -> tuple[expr, Temporaries]:
        if atomic_p:
            new_sym = generate_name("tmp")
            return (Name(new_sym), bindings + [(Name(new_sym), exp)])
        return (exp, bindings)

    def rco_flat(self, rcolist: tuple[expr, Temporaries]) -> List[stmt]:
        stmts = [Assign([atmtp[0]], atmtp[1]) for atmtp in rcolist[1]]
        # print(stmts)
        return stmts

    def rco_atom(self, e:expr) -> tuple[expr, Temporaries]:
        pass

    def rco_exp(self, e: expr, need_atomic: bool) -> tuple[expr, Temporaries]:
        match e:
            case Constant(value):
                new_expr = e
                need_atomic = False
                new_bindings = []
            case Name(id):
                new_expr = e
                need_atomic = False
                new_bindings = []
            case BinOp(latm, Add(), ratm):
                atm1 = self.rco_exp(latm, True)
                atm2 = self.rco_exp(ratm, True)
                new_expr = BinOp(atm1[0], Add(), atm2[0])
                new_bindings = atm1[1] + atm2[1]
            case BinOp(latm, Sub(), ratm):
                atm1 = self.rco_exp(latm, True)
                atm2 = self.rco_exp(ratm, True)
                new_expr = BinOp(atm1[0], Sub(), atm2[0])
                new_bindings = atm1[1] + atm2[1]
            case UnaryOp(USub(), atm):
                atm1 = self.rco_exp(atm, True)
                new_expr = UnaryOp(USub(), atm1[0])
                new_bindings = atm1[1]
            case UnaryOp(Not(), atm):
                atm1 = self.rco_exp(atm, True)
                new_expr = UnaryOp(Not(), atm1[0])
                new_bindings = atm1[1]
            case Call(Name('input_int'), []):
                new_expr = e
                new_bindings = []
            case Compare(latm, [cmp], [ratm]) as c:
                # print(ratm)
                atm1 = self.rco_exp(latm, True)
                atm2 = self.rco_exp(ratm, True)
                new_expr = Compare(atm1[0], [cmp], [atm2[0]])
                new_bindings = atm1[1] + atm2[1]
                print(new_bindings)
            case IfExp(e1, e2, e3):
                atm1 = self.rco_exp(e1, False)
                ss1 = self.rco_stmt(Expr(e2))
                ss2 = self.rco_stmt(Expr(e3))
                # print("ss1:", ss1)
                new_expr = IfExp(atm1[0], Begin(ss1[0:len(ss1)-1], ss1[len(ss1)-1].value),
                                          Begin(ss2[0:len(ss1)-1], ss2[len(ss2)-1].value))
                new_bindings = atm1[1]
        return self.build_atomic_pair(need_atomic, new_expr, new_bindings)

    def rco_stmt(self, s: stmt) -> list[stmt]:
        new_stmts = []
        match s:
            case Expr(Call(Name('print'), [atom])):
                # print(atom)
                rcotp = self.rco_exp(atom, True)
                # print(rcotp)
                new_stmts = self.rco_flat(rcotp)
                new_stmts.append(Expr(Call(Name('print'), [rcotp[0]])))
                # print(new_stmts)
            case Expr(exp):
                rcotp = self.rco_exp(exp, False)
                new_stmts = self.rco_flat(rcotp)
                new_stmts.append(Expr(rcotp[0]))
            case Assign([Name(var)], exp):
                rcotp = self.rco_exp(exp, False)
                # print(rcotp)
                new_stmts = self.rco_flat(rcotp)
                new_stmts.append(Assign([Name(var)], rcotp[0]))
                # print(new_stmts)
            # L_if
            case If(cond, ss1, ss2):
                new_cond_rcotp = self.rco_exp(cond, False)
                new_stmts = self.rco_flat(new_cond_rcotp)
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
                new_stmts.append(If(new_cond_rcotp[0], new_ss1, new_ss2))
            # L_while
            case While(cond, ss1, _):
                new_cond_rcotp = self.rco_exp(cond, False)
                new_stmts = self.rco_flat(new_cond_rcotp)
                new_ss1_temp = [self.rco_stmt(stm) for stm in ss1]
                new_ss1 = []
                for stmts in new_ss1_temp:
                    if stmts:
                        new_ss1 = new_ss1 + stmts
                new_stmts.append(While(new_cond_rcotp[0], new_ss1, []))
        return new_stmts

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
                # print(new_body)
                return Module(new_body)
        
    ############################################################################
    # Explicate Control
    ############################################################################

    def create_block(
        self,
        stmts:List[stmt],
        basic_blocks:Dict[str,List[stmt]]
    ) -> List[stmt]:
        match stmts:
            case [Goto(l)]:
                return stmts
            case _:
                label = label_name(generate_name('block'))
                basic_blocks[label] = stmts
                return [Goto(label)]

    def explicate_effect(
        self,
        e:expr, 
        cont:Stmts,
        basic_blocks:Dict[str,List[stmt]]
    ) -> Stmts:
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
 
    def explicate_assign(
        self,
        lhs,
        rhs,
        cont: Stmts,
        basic_blocks: BasicBlocks
    ) -> Stmts:
        match rhs:
            case IfExp(test, body, orelse):
                # Pack the stmt should be excuted after this assign as a block(?)
                # print(lhs, rhs)
                cont = self.create_block(cont, basic_blocks)
                new_body = self.explicate_assign(lhs, body, cont, basic_blocks)
                new_orelse = self.explicate_assign(lhs, orelse, cont, basic_blocks)
                goto_thn = self.create_block(new_body, basic_blocks)
                goto_els = self.create_block(new_orelse, basic_blocks)
                new_cond = self.explicate_pred(test, goto_thn, goto_els, basic_blocks)
                # Clear cont by the way.
                return new_cond
            case Begin(body, result):
                cont_stmts = [Assign([lhs], result)] + (cont if cont else [])
                goto_cont = self.iterate_on_stmts(body, cont_stmts, basic_blocks)
                return goto_cont             
            case _:
                if (cont == None):
                    print(lhs, rhs)
                return [Assign([lhs], rhs)] + (cont if cont else [])

    def explicate_pred(
        self,
        cnd:expr, 
        thn,
        els,
        basic_blocks
    ) -> Stmts:
        match cnd:
            case Compare(left, [op], [right]):
                return [If(cnd, thn, els)] 
            case Constant(True):
                return thn
            case Constant(False):
                return els 
            case UnaryOp(Not(), operand):
                return [If(operand, els, thn)]
            case IfExp(test, body, orelse):
                goto_then = self.explicate_pred(body.result, thn, els, basic_blocks)
                goto_else = self.explicate_pred(orelse.result, thn, els, basic_blocks)
                goto_body = self.create_block(goto_then, basic_blocks)
                goto_orelse = self.create_block(goto_else, basic_blocks)
                new_test = self.explicate_pred(test, body.body+goto_body, orelse.body+goto_orelse, basic_blocks)
                # print("new test:")
                # print(new_test)
                # cont = self.create_block(cont, basic_blocks)
                return new_test
            case Begin(body, result):
                return body.append(Expr(result))
            case _:
                return [If(Compare(cnd, [Eq()], [Constant(False)]),
                           self.create_block(els, basic_blocks),
                           self.create_block(thn, basic_blocks))]

    # TODO 处理If, While的嵌套statement问题, 下面的实现没有考虑body中是statement.
    def explicate_stmt(
        self,
        s:stmt,
        cont:Stmts,
        basic_blocks:BasicBlocks
    ) -> Stmts:
        match s:
            case Assign([lhs], rhs):
                return self.explicate_assign(lhs, rhs, cont, basic_blocks)
            case Expr(value):
                return self.explicate_effect(value, cont, basic_blocks)
            case If(test, body, orelse):
                # Similar to IfExp
                # If(Compare(atm,[cmp],[atm]), [Goto(label)], [Goto(label)])
                goto_cont = self.create_block(cont, basic_blocks)

                new_body = self.iterate_on_stmts(body, goto_cont, basic_blocks)
                goto_body = self.create_block(new_body, basic_blocks)
                new_orelse = self.iterate_on_stmts(orelse, goto_cont, basic_blocks)
                goto_orelse = self.create_block(new_orelse, basic_blocks)
                new_stmt = self.explicate_pred(test, goto_body, goto_orelse, basic_blocks)
                return new_stmt
            case While(cond, body, _):
                # 为代表while的if手动创建一个block使得可以body block可以在goto中访问
                goto_while = self.create_block([], basic_blocks)

                goto_cont = self.create_block(cont, basic_blocks)
                # Add goto while_label in the end of the body instructions block
                new_body = self.iterate_on_stmts(body, goto_while, basic_blocks)
                goto_body = self.create_block(new_body, basic_blocks)
                # bind while_label with actual corresponding Cif statements
                basic_blocks[goto_while[0].label] = self.explicate_pred(cond,goto_body,goto_cont,basic_blocks)
                # return goto while_label
                return goto_while
    
    def iterate_on_stmts(
        self,
        stmts:Stmts,
        cont:Stmts = [],
        basic_blocks: BasicBlocks = {}
    ) -> Stmts:
        new_seq = cont
        for s in reversed(stmts):
            new_seq = self.explicate_stmt(s, new_seq, basic_blocks)
        return new_seq

    def explicate_control(self, p:Module) -> CProgram(Dict[Label, Stmts]):
        match p:
            case Module(body):
                # TODO This is not right
                new_body = [Return(Constant(0))]
                basic_blocks = {}
                new_body = self.iterate_on_stmts(body, new_body, basic_blocks)
                basic_blocks[label_name('start')] = new_body
                # print(basic_blocks)
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

    # TODO Wut's the Variable Here?
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
        instrs = list()
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
                # print("select_instruciton PASS:")
                # print(X86Program(new_body))
                return X86Program(new_body)
            case CProgram(body):
                new_body:Dict[str, List[instr]] = {}
                for (k,v) in body.items():
                    new_body_temp = [self.select_stmt(stmt) for stmt in v]
                    stmts_temp = []
                    for stmts in new_body_temp:
                        stmts_temp += stmts
                    new_body[k] = stmts_temp
                # new_body["main"] = []
                # new_body["conclusion"] = []
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
            # case Instr(cmd, [arg1, arg2]) if cmd in self.instrs_two:
            case Instr(cmd, [arg1, arg2]):
                return Instr(cmd, [self.assign_homes_arg(arg1, home), self.assign_homes_arg(arg2, home)])
            # case Instr(cmd, [arg1]) if cmd in self.instrs_one:
            case Instr(cmd, [arg1]):
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
                # print(stack_space)
                x86prog.stack_space = stack_space
                x86prog.home = home
                return x86prog

    ############################################################################
    # Patch Instructions
    ############################################################################

    def patch_instr(self, i: instr) -> List[instr]:
        instrs = []
        match i:
            case Instr('movzbq', [arg1, arg2]):
                if isinstance(arg2, Variable):
                    instrs.append(Instr('movzbq', [arg1, Reg('rax')]))
                    instrs.append(Instr('movq', [Reg('rax'), arg2]))
            # case Instr(cmd, [arg1, arg2]) if cmd in self.instrs_two:
            case Instr(cmd, [arg1, arg2]):
                match (arg1, arg2):
                    # Eq to delete the instruction
                    # case (Deref(_) as d1, Deref(_) as d2) \
                    case (d1, d2) if d1 == d2 and cmd in ['movq']:
                        pass
                    case (Deref(_) as d1, Deref(_) as d2):
                        instrs.append(Instr('movq', [arg1, Reg('rax')]))
                        instrs.append(Instr(cmd, [Reg('rax'), arg2]))
                    case (Immediate(x), y):
                        # cmpq
                        if (isinstance(y, Immediate) and cmd == "cmpq"):
                            instrs.append(Instr('movq', [arg1, Reg('rax')]))
                            instrs.append(Instr(cmd, [Reg('rax'), arg2]))
                        if (x > 2**16):
                            instrs.append(Instr('movq', [arg1, Reg('rax')]))
                            instrs.append(Instr(cmd, [Reg('rax'), arg2]))
                        else:
                            instrs.append(i)
                    case _:
                        instrs.append(i)
            case Instr(cmd, [arg1]):
                match arg1:
                    case Immediate(x):
                        if (x > 2**16):
                            instrs.append(Instr('movq', [arg1, Reg('rax')]))
                            instrs.append(Instr(cmd, [Reg('rax')]))
                        else:
                            instrs.append(i)
                    case _:
                        instrs.append(i)
            case _:
                instrs.append(i)
        return instrs

    def patch_instrs(self, ss: List[instr]) -> List[instr]:
        ss = [self.patch_instr(i) for i in ss]
        # print(ss)
        ss = [i for ins in ss for i in ins]
        return ss

    def patch_instructions(self, p: X86Program) -> X86Program:
        match p:
            case X86Program(body):
                for block, instrs in body.items():
                    body[block] = self.patch_instrs(instrs)
                x86prog = p
                x86prog.stack_space = p.stack_space
                x86prog.home = p.home
                return x86prog

    ############################################################################
    # Prelude & Conclusion
    ############################################################################
    
    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        match p:
            case X86Program(body):
                temp1 = []
                temp2 = []
                for r in p.used_callee:
                    temp1.append(Instr('pushq', [r]))
                    temp2.append(Instr('popq', [r]))
                temp2.reverse
                # Prelude Main
                body['main'] = [Instr('pushq', [Reg('rbp')])
                               , Instr('movq', [Reg('rsp'), Reg('rbp')])] \
                               + temp1 \
                               + [Instr('subq', [Immediate(p.stack_space), Reg('rsp')]), Jump("start")]
                # Conclusion
                body["conclusion"] =[Instr('addq', [Immediate(p.stack_space), Reg('rsp')])] \
                                    + temp2 \
                                    + [Instr('popq', [Reg('rbp')])
                                      , Retq()]

                # x86prog = X86Program(body)
                # x86prog.stack_space = p.stack_space
                # x86prog.home = p.home
                return p
