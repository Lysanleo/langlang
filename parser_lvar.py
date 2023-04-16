from lark import *

with open("lvar.lark", "r") as f:
    grammar = f.read()


parser = Lark(grammar, start = "lang_var", parser = "earley", ambiguity = 'explicit')

def parse_lvar(input_str):
    try:
        result = parser.parse(input_str)
        print(f"Parse Tree: \n {result.pretty()}")
    except Exception as e:
        print(e)
        print(f"Invalid input: {input_str}")


if __name__ == '__main__':
    test1 = '''abc=1+2-3\r'''
    parse_lvar(test1)