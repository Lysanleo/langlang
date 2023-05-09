import compiler
from graph import UndirectedAdjList
from typing import List, Tuple, Set, Dict
from ast import *
from x86_ast import *
from typing import Set, Dict, Tuple
from priority_queue import PriorityQueue

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

    def get_arg_vars(self, args) -> Set[location]:
        return {a for a in args if isinstance(a, (Deref, Reg, Variable))}

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
                return set()

    def write_vars(self, i: instr) -> Set[location]:
        match i:
            # W(i) = A(i) - R(i)
            case Instr(_):
                return self.arg_vars(i) - self.read_vars(i)
            case Callq(_, _):
                return set(self.caller_saved_regs)
            case Retq() |\
                 Jump(): 
                return set()


    # L_after(n) = empty when n equals len(instr_list)
    # L_after(k) = L_before(k + 1)
    def compute_la(self, instrs, index: int, map) -> Set[location]:
        if index == len(instrs) - 1: # instrs[index] is the last instr
            return set() # The last instr's L_after = empty
        else:                        # Compute L_before(k+1)
            i = instrs[index+1] # L[index + 1]
            return  (map[i] - self.write_vars(i)) | self.read_vars(i) # L_before(index+1)
        

    def uncover_live(self, p: X86Program) -> Dict[instr, Set[location]]:
        # L_after :: la
        instr_la_map : Dict[instr, Set[location]] = {}
        match p:
            case X86Program(instrs):
                if 'main' in instrs.keys():
                    instrs = instrs['main']
                else:
                    instrs = instrs
                btof = list(range(len(instrs)))
                btof.reverse()
                for i in btof:
                    instr_la_map[instrs[i]] = self.compute_la(instrs, i, instr_la_map)
        return instr_la_map


    ############################################################################
    # Build Interference
    ############################################################################

    def build_interference(self, p: X86Program,
                           live_after: Dict[instr, Set[location]]) -> UndirectedAdjList:
        inter_graph = UndirectedAdjList()
        body = p.get_body()
        instrs = []
        if isinstance(body, dict):
            # main instr only
            instrs = body['main']
        else:
            instrs = body

        # Add edges
        for i in instrs:
            match i:
                case Callq(_,_):
                    # pass
                    for v in live_after[i]:
                        for creg in self.caller_saved_regs:
                            inter_graph.add_edge(v, creg)
                case Instr('movq', [arg1, arg2]):
                    for v in live_after[i]:
                        if v != arg1 and v != arg2:
                            inter_graph.add_edge(v, arg2)
                        inter_graph.add_vertex(v)
                case _:
                    for v in live_after[i]:
                        for d in self.write_vars(i):
                            # v != d
                            if d != v:
                                inter_graph.add_edge(v, d)
                        inter_graph.add_vertex(v)
    
        # v_list = {s for i in instrs for s in live_after[i]}
        return inter_graph

    ############################################################################
    # Allocate Registers
    ############################################################################

    # reg_map :: Integer -> Register
    reg_map = {0: Reg('rcx'), 1: Reg('rdx'), 2: Reg('rsi'), 3: Reg('rdi'),
               4: Reg('r8'), 5: Reg('r9'), 6: Reg('r10'), 7: Reg('rbx'), 
               8: Reg('r12'), 9: Reg('r13'), 10: Reg('r14')}
    # Number of stack variables
    stack_var_num = 0

    # Get a set of Variables from interference graph
    def get_variables(self, graph: UndirectedAdjList) -> Set[location]:
        vars = {lo for lo in graph.vertices() if isinstance(lo, Variable)}
        return vars

    def pretty_print_vrmap(self, vrmap):
        for k, v in vrmap.items():
            print(f"{k} |-> {v[0]}")

    # Returns the coloring and the set of spilled variables.
    def color_graph(self, graph: UndirectedAdjList,
                    variables: Set[location]) -> Tuple[Dict[location, int], Set[location]]:
        # BUG : Hard Code reg_map
        reg_map = self.reg_map
        regints =set(range(0, len(reg_map)))
        location_reg_map = {}
        spilled_variables = set()
        # Indicate the saturation of variable
        L = {l:[None, set()] for l in variables}

        # Define sasturated_node_Q
        # Provide most saturated vertex in variables
        def less(x, y):
            return len(L[x.key][1]) < len(L[y.key][1])
        saturated_v_Q = PriorityQueue(less)
        for k, v in L.items():
            saturated_v_Q.push(k)
        # print(saturated_v_Q)
        # for i in range(0, len(L)):
            # print(saturated_v_Q.pop())

        while saturated_v_Q.empty() == False:
            v = saturated_v_Q.pop()     #Get the most saturaed vertex
            # BUG : Checking if set is empty
            regs_left = list(regints - L[v][1])
            if len(regs_left) == 0:
                spilled_variables.add(v)
                self.stack_var_num += 1
                deref = Deref('rbp', self.stack_var_num * (-8))
                new_map_k = self.stack_var_num - 1 + len(regs_left)
                reg_map[new_map_k] = deref
                regs_left.append(new_map_k)
            target_regint = regs_left[0]
            # Update L[v][0]
            L[v][0] = target_regint
            # Update adjacent L[adj][1]
            # increase adjacent priority in saturated_v_Q
            for adj in graph.adjacent(v):
                if adj in variables:
                    (L[adj][1]).add(target_regint)
                    saturated_v_Q.increase_key(adj)
            # self.pretty_print_vrmap(L)
            # print("\n")
        location_reg_map = {k:v[0] for k,v in L.items()}

        # self.pretty_print_vrmap(L)
        # return (lrmap, set(L.keys()))
        return (location_reg_map, spilled_variables)

    # Select according to map for variable locations
    def select_color(self, a:location, color) -> location:
        loc_regint_map = color[0]
        match a:
            case Variable(var):
                return self.reg_map[loc_regint_map[a]]
            case _:
                return a
            
    def replace_in_instr(self, i: instr, color) -> instr:
        match i:
            case Instr(cmd, [arg1, arg2]) if cmd in self.instrs_two:
                return Instr(cmd, [self.select_color(arg1, color), self.select_color(arg2, color)])
            case Instr(cmd, [arg1]) if cmd in self.instrs_one:
                return Instr(cmd, [self.select_color(arg1, color)])
            case _:
                return i

    def allocate_registers(self, p: X86Program,
                           graph: UndirectedAdjList) -> X86Program:
        body = p.get_body()
        color = self.color_graph(graph, self.get_variables(graph))
        ss = [self.replace_in_instr(i) for i in body]
        x86prog = X86Program(ss)
        return x86prog

    # ############################################################################
    # # Assign Homes
    # ############################################################################

    def assign_homes(self, pseudo_x86: X86Program) -> X86Program:
        graph = self.build_interference(pseudo_x86, self.uncover_live(pseudo_x86))
        x86prog = self.allocate_registers(pseudo_x86, graph)
        return x86prog

    # ###########################################################################
    # # Patch Instructions
    # ###########################################################################

    def patch_instructions(self, p: X86Program) -> X86Program:
        body = p.get_body()
        new_body = self.patch_instrs(body)
        x86prog = X86Program(new_body)
        return x86prog

    # ###########################################################################
    # # Prelude & Conclusion
    # ###########################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        pass
