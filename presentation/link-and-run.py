#!/usr/bin/env python3

import os
import sys
sys.path.append("..") # Adds higher directory to python modules path.
from ast import *


# Check if two arguments are provided
if len(sys.argv) != 2:
    print("Usage: {} <string1> ".format(sys.argv[0]))
    sys.exit(1)

# Assign the arguments to variables
string1 = sys.argv[1]

x86_filename = string1 + ".s"

os.system('gcc runtime.o '+x86_filename+" -o "+string1+".exe")

print(f"生成可执行文件成功: {string1}.exe")
