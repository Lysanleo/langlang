#!/usr/bin/env python3

import os
import sys
sys.path.append("..") # Adds higher directory to python modules path.
from ast import *
from compiler_ltup import CompilerLtup


compiler_ltup = CompilerLtup()

def compile(program:str):
    source_filename = program + ".ll"
    x86_filename = program + ".s"
    with open(source_filename) as source:
        program = parse(source.read())

    p = compiler_ltup.compile(program)

    with open(x86_filename, "w") as dest:
        dest.write(str(p))

# Check if two arguments are provided
if len(sys.argv) != 2:
    print("Usage: {} <string1> ".format(sys.argv[0]))
    sys.exit(1)

# Assign the arguments to variables
string1 = sys.argv[1]

compile(string1)

print(f"编译成功: {string1}.s")
