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
            case Subscript(exp, index_expr, Load()):
                new_exp_rcotp = self.rco_exp(exp, True)
                # new_index_expr_rcotp = self.rco_exp(index_expr, True)
                new_expr = Subscript(new_exp_rcotp[0], index_expr, Load())
                new_bindings = new_exp_rcotp[1]
            case Allocate(length, typ):
                new_expr = Allocate(length, typ)
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
