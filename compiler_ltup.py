import compiler
from ast import *
from utils import *
from x86_ast import *
import x86_ast

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
                inits_assign_pairs = [(init_name, exprs[i]) for i,init_name in inits.items()]
                # assign statements
                sub_assigns = make_assigns(subscript_assign_pairs)
                init_assigns = make_assigns(inits_assign_pairs)
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
            case Subscript(exp, Constant(index), Load()):
                new_exp = self.handle_ltup_expr(exp)
                new_expr = Subscript(new_exp, Constant(index), Load())
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
