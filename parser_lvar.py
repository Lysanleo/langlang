from lark import *
from ast import *
from typing import List

with open("lvar.lark", "r") as f:
    grammar = f.read()


parser = Lark(grammar, start = "lang_var", parser = "earley", ambiguity = 'explicit')

def parse_lvar(input_str):
    try:
        result = parser.parse(input_str)
        # print(input_str)
        # print(result)
        return result
    except Exception as e:
        print(e)
        print(f"Invalid input: {input_str}")

def print_tree(parse_result):
    print(f"Parse Tree: \n {parse_result.pretty()}")

def filter_ast(xss):
    return list(filter(lambda x: x!=None, xss))

def flat_ast(xss):
    for x in xss:
        if isinstance(x, List):
            yield from flat_ast(x)
        else:
            yield x

def parse_tree_to_ast(e):
    if e.data == 'int':
        return Constant(int(e.children[0].value))
    if e.data == 'var':
        return Name(e.children[0].value)
    elif e.data == 'input_int':
        return Call(Name('input_int'), [])
    elif e.data == 'add':
        e1, e2 = e.children
        return BinOp(parse_tree_to_ast(e1), Add(), parse_tree_to_ast(e2))
    elif e.data == 'sub':
        e1, e2 = e.children
        return BinOp(parse_tree_to_ast(e1), Sub(), parse_tree_to_ast(e2))
    elif e.data == 'usub':
        e1, = e.children
        return UnaryOp(USub(), parse_tree_to_ast(e1))
    elif e.data == 'paren':
        pass
    elif e.data == 'print':
        e1, = e.children
        return Expr(Call(Name('print'),[parse_tree_to_ast(e1)]))
    elif e.data == 'assign':
        e1, e2 = e.children
        return Assign([parse_tree_to_ast(e1)], parse_tree_to_ast(e2))
    elif e.data == 'expr':
        e1, = e.children
        return Expr(parse_tree_to_ast(e1))
    elif e.data == 'exp':
        e1, = e.children
        return parse_tree_to_ast(e1)
    elif e.data == 'empty_stmt':
        return None # TODO Needs to be filterd
    elif e.data == "newline":
        return None
    elif e.data == 'add_stmt':
        raw_ast = [parse_tree_to_ast(e1) for e1 in e.children]
        return raw_ast
    elif e.data == 'module':
        e1, = e.children
        # It will be helpful to have Monad
        nested_ast = parse_tree_to_ast(e1)
        flatted_ast = flat_ast(nested_ast)
        # print(flatted_ast)
        filtered_ast = filter_ast(flatted_ast)
        return Module(filtered_ast)
    else:
        raise Exception('unhandled parse tree', e)

def parse(input):
    # print(input)
    s1 = parse_lvar(input)
    # print(s1)
    s2 = parse_tree_to_ast(s1)
    return s2

if __name__ == '__main__':
    test1 = '''abc=1+2-3\n'''
    test2 = '''abc = -114 + 514 - (39 -42)\n
               print(abc)\n'''
    test3 = '''1\n
               2\n'''
    print_tree(parse_lvar(test1))
    print(parse_lvar(test1).__str__())

    print_tree(parse_lvar(test2))
    print(parse_lvar(test2).__str__())
    print_tree(parse_lvar(test3))
    print(parse_lvar(test3).__str__())

    test4 = '''
    a = 10 + 10
    print(0)
    '''
    print(parse_lvar(test4))