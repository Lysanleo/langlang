#!/usr/bin/env python3

import os
import sys

# Check if two arguments are provided
if len(sys.argv) != 3:
    print("Usage: {} <string1> <string2>".format(sys.argv[0]))
    sys.exit(1)

# Assign the arguments to variables
string1 = sys.argv[1]
string2 = sys.argv[2]

# Create the directory if it doesn't exist
directory = os.path.join("tests", string1)
os.makedirs(directory, exist_ok=True)

file_sufix = ['.py', '.in', '.out', '.golden']

for suf in file_sufix:
    with open(os.path.join(directory, string2 + suf), "w") as f:
        pass

print("Files created successfully!")
