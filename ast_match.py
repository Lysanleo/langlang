def handle_exp(e:exp) -> exp:
    match e:
        case BinOp(lhs_exp, op, rhs_exp):
            pass
        case UnaryOp(op, rhs_exp):
            pass
        case BoolOp(boolop, [exp1, exp2]):
            pass
        case IfExp(cond_exp, then_exp, orelse_exp):
            pass
        case Name(varname_str):
            pass
        case Compare(lhs_exp, [cmp], [rhs_exp]):
            pass
        case Tuple(exprs, Load()):
            pass
        case Subscript(exp, Constant(index), Load()):
            pass
        case Call(Name('len'), [exp]):
            pass


def handle_stmt(s:stmt) -> stmt:
    match s:
        case Expr(exp):
            pass
        case While(cond_exp, bodystmts, []):
            pass
        case If(cond_exp, then_stmts, orelse_stmts):
            pass
        case Assign([lhs], rhs_exp):
            pass
        case _:
            new_stmt = s
    return new_stmt

