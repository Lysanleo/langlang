import compiler
from graph import UndirectedAdjList
from typing import List, Tuple, Set, Dict
from ast import *
from x86_ast import *
from typing import Set, Dict, Tuple

# Skeleton code for the chapter on Register Allocation

class Compiler(compiler.Compiler):

    ###########################################################################
    # Uncover Live
    ###########################################################################

    caller_saved_regs = [Reg('rax'),Reg('rcx'),Reg('rdx'),
                         Reg('rsi'),Reg('rdi'),Reg('r8'),
                         Reg('r9'),Reg('r10'),Reg('r11')]
    argument_regs = [Reg('rdi'), Reg('rsi'), Reg('rdx'),
                     Reg('rcx'), Reg('r8'), Reg('r9')]

    def get_arg_vars(self, args: List[arg]) -> Set[location]:
        return {a for a in args if isinstance(a, (Deref, Reg))}

    def arg_vars(self, i: instr) -> Set[location]:
        match i:
            case Instr('addq', [arg1, arg2]) |\
                 Instr('subq', [arg1, arg2]):
                return self.get_arg_vars([arg1, arg2])
            case Instr('movq', [arg1, arg2]):
                return self.get_arg_vars([arg1, arg2])
            case Instr('negq', [arg1]):
                return self.get_arg_vars([arg1])
            case Instr('pushq', [arg1]):
                return self.get_arg_vars([arg1])
            case Instr('popq', [arg1]):
                return self.get_arg_vars([arg1])

    def read_vars(self, i: instr) -> Set[location]:
        match i:
            case Instr('addq', [arg1, arg2]) |\
                 Instr('subq', [arg1, arg2]):
                return self.get_arg_vars([arg1, arg2])
            case Instr('movq', [arg1, arg2]):
                return self.get_arg_vars([arg1])
            case Instr('negq', [arg1]):
                return self.get_arg_vars([arg1])
            case Instr('pushq', [arg1]):
                return self.get_arg_vars([arg1])
            case Instr('popq', [arg1]):
                return self.get_arg_vars([arg1])
            case Callq(_, n):
                return set(self.argument_regs[0:n]) # [0:arity] of argument regs
            case Retq() |\
                 Jump(): 
                return {}

    def write_vars(self, i: instr) -> Set[location]:
        match i:
            # W(i) = A(i) - R(i)
            case Instr(_):
                return self.arg_vars(i) - self.read_vars(i)
            case Callq(_, _):
                return set(self.caller_saved_regs)
            case Retq() |\
                 Jump(): 
                return {}


    # L_after(n) = empty when n equals len(instr_list)
    # L_after(k) = L_before(k + 1)
    def compute_la(self, instrs: List[instr], index: int, map) -> Set[location]:
        if index == len(instrs) - 1: # instrs[index] is the last instr
            return {} # The last instr's L_after = empty
        else:                        # Compute L_before(k+1)
            i = instrs[index+1] # L[index + 1]
            return  (map[i] - self.write_vars(i)) | self.read_vars(i) # L_before(index+1)
        

    def uncover_live(self, p: X86Program) -> Dict[instr, Set[location]]:
        instr_la_map : Dict[instr, Set[location]] = {}
        match p:
            case X86Program(instrs):
                btof = list(range(len(instrs))).reverse()
                for i in btof:
                    instr_la_map[instrs[i]] = \
                        self.compute_la(instrs, i, instr_la_map)
        return instr_la_map


    ############################################################################
    # Build Interference
    ############################################################################

    def build_interference(self, p: X86Program,
                           live_after: Dict[instr, Set[location]]) -> UndirectedAdjList:
        # YOUR CODE HERE
        pass

    ############################################################################
    # Allocate Registers
    ############################################################################

    # Returns the coloring and the set of spilled variables.
    def color_graph(self, graph: UndirectedAdjList,
                    variables: Set[location]) -> Tuple[Dict[location, int], Set[location]]:
        # YOUR CODE HERE
        pass

    def allocate_registers(self, p: X86Program,
                           graph: UndirectedAdjList) -> X86Program:
        # YOUR CODE HERE
        pass

    ############################################################################
    # Assign Homes
    ############################################################################

    def assign_homes(self, pseudo_x86: X86Program) -> X86Program:
        # YOUR CODE HERE
        pass

    ###########################################################################
    # Patch Instructions
    ###########################################################################

    def patch_instructions(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        pass

    ###########################################################################
    # Prelude & Conclusion
    ###########################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        pass
