from ast import *
from utils import *
from x86_ast import *
import x86_ast
from typing import List, Set, Dict

Binding = tuple[Name, expr]
Temporaries = list[Binding]

Label = str
Stmts = list[stmt]
BasicBlocks = Dict[Label,Stmts]

