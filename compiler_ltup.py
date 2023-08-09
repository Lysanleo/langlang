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

    ############################################################################
    # Remove Complex Operands
    ############################################################################


    def rco_flat(self, rcolist: tuple[expr, Temporaries]) -> List[stmt]:
        stmts = [Assign([atmtp[0]], atmtp[1]) for atmtp in rcolist[1]]
        # print(stmts)
        return stmts

    def rco_atom(self,e:expr) -> tuple[expr, Temporaries]:
        pass

    def rco_exp(self, e: expr, need_atomic: bool) -> tuple[expr, Temporaries]:
        new_sym = ""
        match e:
            case Constant(value):
                return (e, [])
            case Name(id):
                # return (e, [(e, e)])
                return (e, [])
            case Begin(body_stmts, ret_expr):
                pass
                
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
                    return (Name(new_sym), new_bindings + [(Name(new_sym), new_expr)])
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
            case Compare(latm, [cmp], [ratm]) as c:
                print(ratm)
                atm1 = self.rco_exp(latm, True)
                atm2 = self.rco_exp(ratm, True)
                new_expr = Compare(atm1[0], [cmp], [atm2[0]])
                new_bindings = atm1[1] + atm2[1]
                print(new_bindings)
                if need_atomic:
                    new_sym = generate_name("tmp")
                    return (Name(new_sym), new_bindings + [(Name(new_sym), new_expr)])
                return (new_expr, new_bindings)
            case IfExp(e1, e2, e3):
                atm1 = self.rco_exp(e1, False)
                ss1 = self.rco_stmt(Expr(e2))
                ss2 = self.rco_stmt(Expr(e3))
                # print("ss1:", ss1)
                new_expr = IfExp(atm1[0], Begin(ss1[0:len(ss1)-1], ss1[len(ss1)-1].value),
                                          Begin(ss2[0:len(ss1)-1], ss2[len(ss2)-1].value))
                new_bindings = atm1[1]
                if need_atomic:
                    new_sym = generate_name("tmp")
                    new_bindings = new_bindings + [(Name(new_sym), new_expr)]
                    return (Name(new_sym), new_bindings)
                return (new_expr, new_bindings)

    def rco_stmt(self, s: stmt) -> list[stmt]:
        match s:
            case Expr(Call(Name('print'), [atom])):
                # rcotp :: rcotemp
                rcotp = self.rco_exp(atom, True)
                new_exprs = self.rco_flat(rcotp)
                new_exprs.append(Expr(Call(Name('print'), [rcotp[0]])))
                # print(new_exprs)
                return new_exprs
            case Expr(exp):
                rcotp = self.rco_exp(exp, False)
                new_exprs = self.rco_flat(rcotp)
                new_exprs.append(Expr(rcotp[0]))
                return new_exprs
            case Assign([lhs], rhs_exp):
                rcotp = self.rco_exp(rhs_exp, False)
                # print(rcotp)
                new_exprs = self.rco_flat(rcotp)
                new_exprs.append(Assign([lhs], rcotp[0]))
                # print(new_exprs)
                return new_exprs
            # L_if
            case If(cond, ss1, ss2):
                rcotp = self.rco_exp(cond, False)
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
            # L_while
            case While(cond, ss1, _):
                rcotp = self.rco_exp(cond, False)
                new_exprs = self.rco_flat(rcotp)
                new_ss1_temp = [self.rco_stmt(stm) for stm in ss1]
                new_ss1 = []
                for stmts in new_ss1_temp:
                    if stmts:
                        new_ss1 = new_ss1 + stmts
                new_exprs.append(While(rcotp[0], new_ss1, []))
                return new_exprs

    def remove_complex_operands(self, p: Module) -> Module:
        match p:
            case Module(body):
                new_body = []
                new_body_temp = [self.rco_stmt(s) for s in body]
                # print(new_body_temp == [None]) => True
                for stmts in new_body_temp:
                    new_body = new_body + stmts
        return Module(new_body)