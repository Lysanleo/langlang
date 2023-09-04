import re
from types import GenericAlias
import compiler
from ast import *
from utils import *
from x86_ast import *
import x86_ast
from data_type import *

class CompilerLtup(compiler.Compiler):

    ############################################################################
    # Expose Allocation
    ############################################################################

    def handle_ltup_expr(self, e:expr) -> expr:
        match e:
            # Trans to the L_alloc
            case Tuple(exprs, Load()):
                # notice that in the eoc alloc has a smaller index than inits
                alloc_name = Name(generate_name("alloc"))
                # inits
                # inits = [(Name(generate_name("init")), exp) for exp in exprs]
                inits = {i:Name(generate_name("init")) for i,_ in enumerate(exprs)}
                # calculate bytes
                bytes = 8 + 8 * len(exprs)
                # condictional allocate call
                cond = Compare(BinOp(GlobalValue("free_ptr"),Add(),Constant(bytes))
                              ,[Lt()]
                              ,[GlobalValue("fromspace_end")])
                body = []
                orelse = [Collect(bytes)]
                conditional_call = If(cond, body, orelse)
                # allocate assign
                alloc_assign = Assign([alloc_name], Allocate(len(exprs), e.has_type))
                # assign pairs
                subscript_assign_pairs = [(Subscript(alloc_name, Constant(i), Store()), init_name) for i,init_name in inits.items()]
                inits_assign_pairs = [(init_name, self.handle_ltup_expr(exprs[i])) for i,init_name in inits.items()]
                # assign statements
                init_assigns = make_assigns(inits_assign_pairs)
                sub_assigns = make_assigns(subscript_assign_pairs)
                # append allocation statements
                cont_stmts:list = init_assigns \
                                + [conditional_call] \
                                + [alloc_assign] \
                                + sub_assigns
                # Completed allocation expression
                new_expr = Begin(cont_stmts, alloc_name)
            case BinOp(lhs_exp, op, rhs_exp):
                new_lhs_exp = self.handle_ltup_expr(lhs_exp)
                new_rhs_exp = self.handle_ltup_expr(rhs_exp)
                new_expr = BinOp(new_lhs_exp, op, new_rhs_exp)
            case UnaryOp(op, rhs_exp):
                new_rhs_exp = self.handle_ltup_expr(rhs_exp)
                new_expr = UnaryOp(op, new_rhs_exp)
            case BoolOp(boolop, [exp1, exp2]):
                new_exp1 = self.handle_ltup_expr(exp1)
                new_exp2 = self.handle_ltup_expr(exp2)
                new_expr = BoolOp(boolop, [new_exp1, new_exp2])
            case IfExp(cond_exp, then_exp, orelse_exp):
                new_cond_exp = self.handle_ltup_expr(cond_exp)
                new_then_exp = self.handle_ltup_expr(then_exp)
                new_orelse_exp = self.handle_ltup_expr(orelse_exp)
                new_expr = IfExp(new_cond_exp, new_then_exp, new_orelse_exp)
            case Compare(lhs_exp, [cmp], [rhs_exp]):
                new_lhs_exp = self.handle_ltup_expr(lhs_exp)
                new_rhs_exp = self.handle_ltup_expr(rhs_exp)
                new_expr = Compare(new_lhs_exp, [cmp], [new_rhs_exp])
            case Subscript(exp, index_expr, ctx):
                new_exp = self.handle_ltup_expr(exp)
                new_index_expr = self.handle_ltup_expr(index_expr)
                new_expr = Subscript(new_exp, new_index_expr, ctx)
            case Call(Name('len'), [exp]):
                new_exp = self.handle_ltup_expr(exp)
                new_expr = Call(Name('len'), [new_exp])
            case _:
                new_expr = e
        return new_expr
    
    def handle_ltup_stmt(self, s:stmt) -> stmt:
        match s:
            case Expr(exp):
                new_stmt = Expr(self.handle_ltup_expr(exp))
            case While(cond_exp, bodystmts, []):
                new_cond_exp = self.handle_ltup_expr(cond_exp)
                new_bodystmts = [self.handle_ltup_stmt(stm) for stm in bodystmts]
                new_stmt = While(new_cond_exp, new_bodystmts, [])
            case If(cond_exp, then_stmts, orelse_stmts):
                new_cond_exp = self.handle_ltup_expr(cond_exp)
                new_then_stmts = [self.handle_ltup_stmt(stm) for stm in then_stmts]
                new_orelse_stmts = [self.handle_ltup_stmt(stm) for stm in orelse_stmts]
                new_stmt = If(new_cond_exp, new_then_stmts, new_orelse_stmts)
            case Assign([lhs_var_exp], rhs_exp):
                new_rhs_exp = self.handle_ltup_expr(rhs_exp)
                new_stmt = Assign([lhs_var_exp], new_rhs_exp)
            case _:
                new_stmt = s
        return new_stmt

    # L_tup -> L_Alloc
    def expose_allocation(self, p:Module) -> Module:
        match p:
            case Module(body):
                new_body = [self.handle_ltup_stmt(s) for s in body]
        return Module(new_body)

    ############################################################################
    # Remove Complex Operands
    ############################################################################

    def rco_exp(self, e: expr, need_atomic: bool) -> tuple[expr, Temporaries]:
        match e:
            case GlobalValue(name):
                new_expr = GlobalValue(name)
                new_bindings = []
            case Begin(body_stmts, ret_expr):
                # -> (new_e, [])
                new_body_stmts_temp = [self.rco_stmt(stm) for stm in body_stmts]
                new_body_stmts = list()
                for stmts in new_body_stmts_temp:
                    if stmts:
                        new_body_stmts = new_body_stmts + stmts
                new_expr = Begin(new_body_stmts, ret_expr)
                new_bindings = []
            case Subscript(exp, idx_expr, Load()):
                new_exp_rcotp = self.rco_exp(exp, True)
                # new_index_expr_rcotp = self.rco_exp(index_expr, True)
                new_expr = Subscript(new_exp_rcotp[0], idx_expr, Load())
                new_bindings = new_exp_rcotp[1]
            case Allocate(length, typ):
                new_expr = e
                new_bindings = []
            case Call(Name('len'), [exp]):
                new_exp_rcotp = self.rco_exp(exp, True)
                new_expr = Call(Name('len'), [new_exp_rcotp[0]])
                new_bindings = new_exp_rcotp[1]
            case _:
                return super().rco_exp(e, need_atomic)
        return self.build_atomic_pair(need_atomic, new_expr, new_bindings)
                
    def rco_stmt(self, s: stmt) -> list[stmt]:
        match s:
            case Assign([Subscript(exp, index_expr, Store())], rhs_exp):
                new_exp_rcotp = self.rco_exp(exp, True)
                # new_index_expr_rcotp = self.rco_exp(index_expr, True)
                new_rhs_exp_rcotp = self.rco_exp(rhs_exp, True)
                new_stmts = [Assign([Subscript(new_exp_rcotp[0], index_expr, Store())], new_rhs_exp_rcotp[0])]
            case Collect(size):
                new_stmts = [s]
            case _:
                return super().rco_stmt(s)
        return new_stmts

    def remove_complex_operands(self, p: Module) -> Module:
        match p:
            case Module(body):
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

    def explicate_stmt(
        self,
        s:stmt,
        cont:Stmts,
        basic_blocks:BasicBlocks
    ) -> Stmts:
        match s:
            case Collect(size):
                return [s] + (cont if cont else [])
            case _:
                return super().explicate_stmt(s, cont, basic_blocks)

    def explicate_control(self, p:Module) -> CProgram(Dict[Label, Stmts]):
        match p:
            case Module(body):
                return super().explicate_control(p)

    ############################################################################
    # Select Instructions
    ############################################################################

    def compute_tuple_tag(self, tup_type:TupleType) -> int:
        # type_args = tup_type.__args__
        # type_str = map(lambda x: str(x), type_args)
        length = len(tup_type.types)
        # prog = re.compile(r"^tuple\[")
        # pt_list = zip(map(lambda x: prog.match(x)!=None, type_str),range(0,length))
        pt_list = zip(map(lambda x: isinstance(x, TupleType), tup_type.types),range(0,length))
        pt_mask = sum(map(lambda pr: 1<<(pr[1]+7) if pr[0] else 0, pt_list))
        return pt_mask + (length << 1) + 1

    def assign_helper(
        self, 
        target: list | str, 
        # idx: int,
        rhs: expr,
        Variable,
        # lhs_tuple_p: bool
    ) -> List[instr]:
        instrs = list()
        match target:
            case [Subscript(Name(var), Constant(i), Store())]:
                instrs.append(Instr('movq', [Variable(var+"'"), Reg('r11')]))
                instrs.append(Instr('movq', [self.select_arg(rhs), Deref('r11', 8*(i+1))]))
            # case [Name(var)] if isinstance(rhs, Subscript):
            case [Name(var)]:
                match rhs:
                    case Subscript(Name(rhs_tuple), Constant(i), _):
                        instrs.append(Instr('movq', [Variable(rhs_tuple+"'"), Reg('r11')]))
                        instrs.append(Instr('movq', [Deref('r11', 8*(i+1)), Variable(var+"'")]))
                    # RHS is allocate
                    case Allocate(bytes, tup_type):
                        # print(tup_type)
                        # print(isinstance(tup_type, GenericAlias))
                        # print(tup_type.types)
                        instrs.append(Instr('movq', [Global('free_ptr'), Reg('r11')]))
                        instrs.append(Instr('addq', [Immediate(8*(bytes+1)), Global('free_ptr')]))
                        instrs.append(Instr('movq', [Immediate(self.compute_tuple_tag(tup_type)), Deref('r11', 0)]))
                        instrs.append(Instr('movq', [Reg('r11'), Variable(var+"'")]))
                    case Compare(operand1, [Is() as cmp], operand2):
                        cc = self.cmp_helper(cmp)
                        instrs = [Instr("cmpq", [operand2, operand1])]
                        instrs.append(Instr("set"+cc, [ByteReg('al')]))
                        instrs.append(Instr("movzbq", [ByteReg('al'), Variable(var)]))
                        return instrs
                    case GlobalValue(gv):
                        instrs.append(Instr('movq', [Global('free_ptr'), Variable(var)]))
                    case _:
                        instrs = super().assign_helper(var, rhs, Variable)
            case _:
                # print(target, rhs)
                instrs = super().assign_helper(target, rhs, Variable)
        return instrs

    # def select_instr(self, e: expr) -> List[instr]:
        # match
        # return super().select_instr(e)

    def select_stmt(self, s:stmt) -> List[instr]:
        instrs = list()
        # print(s)
        match s:
            # Tuple write form
            case Assign([Subscript(Name(var), Constant(i), Store())] as lhs, expr):
                # instrs = self.assign_helper(var, i, expr, Variable, True)
                instrs = self.assign_helper(lhs, expr, Variable)
            case Assign([Name(var)] as lhs, expr):
                instrs = self.assign_helper(lhs, expr, Variable)
            case Expr(Collect(bytes)):
                instrs.append(Instr('movq', [Reg('r15'), Reg('rdi')]))
                instrs.append(Instr('movq', [Immediate(bytes), Reg('rsi')]))
                instrs.append(Callq('collect', 1))
            case Collect(byte_size):
                instrs.append(Instr('movq', [Reg('r15'), Reg('rdi')]))
                instrs.append(Instr('movq', [Immediate(byte_size), Reg('rsi')]))
                instrs.append(Callq("collect", 1))
            case _:
                instrs = super().select_stmt(s)
        return instrs
    
    def select_instructions(self, p: Module | CProgram) -> X86Program:
        return super().select_instructions(p)