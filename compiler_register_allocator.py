import compiler
import math
from graph import *
from typing import List, Tuple, Set, Dict
from ast import *
from x86_ast import *
from typing import Set, Dict, Tuple, List
from priority_queue import PriorityQueue


Label = str
# Skeleton code for the chapter on Register Allocation

class Compiler(compiler.Compiler):

    ###########################################################################
    # CFG
    ###########################################################################

    def __get_jump(self, instrs: List[Instr]) -> List[str]:
        labels = []
        for ins in instrs:
            match ins:
                case Jump(label):
                    labels.append(label)
                case JumpIf(_, label):
                    labels.append(label)
                case _:
                    pass
        return labels

    def build_CFG(self, instrs:Dict[str, List[Instr]]) -> List[Vertex]:
        cfg = DirectedAdjList()
        for label, inss in instrs.items():
            labels = self.__get_jump(inss)
            if labels:
                for in_v in labels: 
                    cfg.add_edge(label, in_v)
            else:
                cfg.add_vertex(label)
        return cfg

    ###########################################################################
    # Uncover Live
    ###########################################################################
    cer_regs = ['rax', 'rcx', 'rdx', 'rsi', 'rdi', 'r8', 'r9', 'r10', 'r11']
    cee_regs = ['rsp', 'rbp', 'rbx', 'r12', 'r13', 'r14', 'r15']

    caller_saved_regs = [Reg(reg) for reg in cer_regs]
    callee_saved_regs = [Reg(reg) for reg in cee_regs]
                        
    argument_regs = [Reg('rdi'), Reg('rsi'), Reg('rdx'),
                     Reg('rcx'), Reg('r8'), Reg('r9')]
    byte_regs = [ByteReg(name) for name in ['ah', 'al', 'bh', 'bl', 'ch', 'cl', 'dh', 'dl']]
    set_instrs = ["set"+cc for cc in ['e' , 'ne' , 'l' , 'le' , 'g' , 'ge']]

    def get_arg_vars(self, args) -> Set[location]:
        return {a for a in args if isinstance(a, (Deref, Variable))}

    def arg_vars(self, i: instr) -> Set[location]:
        match i:
            case Instr('addq', [arg1, arg2]) |\
                 Instr('subq', [arg1, arg2]) |\
                 Instr('movq', [arg1, arg2]) |\
                 Instr('xorq', [arg1, arg2]) |\
                 Instr('cmpq', [arg1, arg2]) |\
                 Instr('movzbq', [arg1, arg2]):
                return self.get_arg_vars([arg1, arg2])
            case Instr('negq', [arg1])  |\
                 Instr('pushq', [arg1]) |\
                 Instr('popq', [arg1]):
                return self.get_arg_vars([arg1])
            case Instr(sets, [arg1]) if sets in self.set_instrs:
                return self.get_arg_vars([arg1])
            case JumpIf(_, label):
                return set()

    def read_vars(self, i: instr) -> Set[location]:
        match i:
            case Instr('addq', [arg1, arg2]) |\
                 Instr('subq', [arg1, arg2]):
                return self.get_arg_vars([arg1, arg2])
            # `movq` does not read from any variables
            case Instr('movq', [arg1, arg2]):
                return self.get_arg_vars([arg1])
            case Instr('negq', [arg1])  |\
                 Instr('pushq', [arg1]) |\
                 Instr('popq', [arg1]):
                return self.get_arg_vars([arg1])
            #TODO 下面关于Lif的部分先乱写
            case Instr('xorq', [arg1, arg2]):
                return self.get_arg_vars([arg1, arg2])
            case Instr('cmpq', [arg1, arg2]):
                return self.get_arg_vars([arg1, arg2])
            case Instr('movzbq', [arg1, arg2]):
                return self.get_arg_vars([arg1, arg2])
            case Instr(sets, [arg1]) if sets in self.set_instrs:
                return self.get_arg_vars([arg1])
            case JumpIf(_, label):
                return set()
            case Callq(_, n):
                return set(self.argument_regs[0:n]) # [0:arity] of argument regs
            case Retq() |\
                 Jump(): 
                return set()

    def write_vars(self, i: instr) -> Set[location]:
        match i:
            # W(i) = A(i) - R(i)
            case Instr('movq', [arg1, arg2]):
                return set([arg2])
            case Instr(_):
                return self.arg_vars(i) - self.read_vars(i)
            case Callq(_, _):
                return set(self.caller_saved_regs)
            case Retq() |\
                 Jump() |\
                 JumpIf(): 
                return set()

    # L_after(n) = empty when n equals len(instr_list)
    # L_after(k) = L_before(k + 1)
    def compute_la(self, instrs:List[Instr], index:int,
                   la_map:Dict[int,Set[location]], lb_block:Dict[str,Set[location]]):
        i = instrs[index]
        res = set()
        instr_num = len(instrs) 
        match i:
            case Jump(label):
                res = lb_block[label]
            case JumpIf(_, label):
                next_lb = set()
                if (index == instr_num - 1):
                    next_lb = set()
                else:
                    i = instrs[index+1]
                    next_lb = (la_map[index+1] - self.write_vars(i)) | self.read_vars(i)
                res = lb_block[label] | next_lb
            case _:
                if index == len(instrs) - 1:
                    res = set()
                else: # Compute L_before(k+1)
                    res = (la_map[index+1] - self.write_vars(i)) | self.read_vars(i)
        return res
    
    cfg = None
    # TODO
    # 1. Modify the instr_la_map to Dict[label, Dict[int, Set[location]]]
    def uncover_live(self, p: X86Program) -> Dict[Label, Dict[int, Set[location]]]:
        # L_after :: la
        live_before_block : Dict[Label, Set[location]] = {}
        match p:
            case X86Program(instrs) if isinstance(instrs, Dict):
                instr_la_map : Dict[Label, Dict[int, Set[location]]] = \
                        dict([(key, {}) for key in instrs.keys()])
                self.cfg = self.build_CFG(instrs)
                rev_topo = topological_sort(transpose(self.cfg))
                # rev_topo.remove("conclusion")
                # Traverse the reverse topo
                # Append live_before_block and live_after_map
                for blk in rev_topo:
                    # Handle main and conclusion block may be Empty
                    if blk in ["conclusion", "main"]:
                        live_before_block[blk] = set()
                        continue
                    inss = instrs[blk]
                    # print(blk)
                    intr_num = len(inss)
                    btof = list(range(intr_num))
                    btof.reverse()
                    # From n-1 to 0
                    for i in btof:
                        instr_la_map[blk][i] = \
                                    self.compute_la(inss, i, instr_la_map[blk], live_before_block)
                        if i == 0: live_before_block[blk] = instr_la_map[blk][i]
        # print(instr_la_map)
        # for i in range(len(instrs['start'])):
            # print(f"{instrs['start'][i]}                     {instr_la_map['start'][i]}")
        return instr_la_map


    ############################################################################
    # Build Interference
    ############################################################################

    def build_interference(self, p: X86Program,
                           live_after: Dict[Label, Dict[int, Set[location]]]) -> UndirectedAdjList:
        inter_graph = UndirectedAdjList()
        body = p.get_body()
        topo = topological_sort(self.cfg)
        instrs = []
        # if isinstance(body, dict):
            # for blk in topo:
                # pass
        for blk in topo:
            instrs = body[blk] if not (blk in ["conclusion", "main"]) else []
            for i in range(len(instrs)):
                match instrs[i]:
                    case Callq(_,_):
                        for v in live_after[blk][i]:
                            for creg in self.caller_saved_regs:
                                # print(v, "edging")
                                inter_graph.add_edge(v,creg)
                    case Instr('movq', [arg1, arg2]):
                        for v in live_after[blk][i]:
                            if v != arg1 and v != arg2:
                                inter_graph.add_edge(v, arg2)
                            inter_graph.add_vertex(v)
                    case Instr('movzbq', [arg1, arg2]):
                        for v in live_after[blk][i]:
                            if v != arg1 and v != arg2:
                                inter_graph.add_edge(v, arg2)
                            inter_graph.add_vertex(v)
                    case _:
                        for v in live_after[blk][i]:
                            for d in self.write_vars(instrs[i]):
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
    allocated_cee_regs = set()    # Allocated callee registers
    stack_var_num = 0          # Number of stack variables
    # mini_stack_location = 0    # Minimum Stack location number

    # Get a set of Variables from interference graph
    def get_variables(self, graph: UndirectedAdjList) -> Set[location]:
        vars = {lo for lo in graph.vertices() if isinstance(lo, Variable)}
        return vars

    def pretty_print_vrmap(self, vrmap):
        for k, v in vrmap.items():
            print(f"{k} |-> {v[0]}")

    # Returns the coloring and the set of spilled variables.
    # TODO: Handle stack allocate
    def color_graph(self, graph: UndirectedAdjList,
                    variables: Set[location]) -> Tuple[Dict[location, int], Set[location]]:
        # BUG : Hard Code reg_map
        reg_map = self.reg_map
        regints:set[int] =set(range(len(reg_map)))
        location_reg_map = {}
        spilled_variables = set()
        
        def get_adjacent_reg_map_int(variable: Variable) -> set[location]:
            regs = set(reg_map.values())
            edged_caller_regs = regs & set(graph.adjacent(variable))
            caller_reg_ints = {i for i in reg_map if reg_map[i] in edged_caller_regs}
            return caller_reg_ints
        # Indicate the saturation for each variables
        L = {l:[None, get_adjacent_reg_map_int(l)] for l in variables}

        # Define sasturated_node_Q
        # Provide most saturated vertex in interference graph
        def less(x, y):
            return len(L[x.key][1]) < len(L[y.key][1])
        saturated_v_Q = PriorityQueue(less)
        for k, v in L.items():
            saturated_v_Q.push(k)

        # Test of PriorityQueue
        # print(saturated_v_Q)
        # for i in range(0, len(L)):
            # print(saturated_v_Q.pop())

        while saturated_v_Q.empty() == False:
            v = saturated_v_Q.pop()     #Get the most saturaed vertex
            # BUG : Checking if avaliable register set is empty
            regs_left = list(regints - L[v][1])
            if len(regs_left) == 0:
                self.stack_var_num += 1
                deref = Deref('rbp', self.stack_var_num * (-8))
                new_map_k = self.stack_var_num - 1 + len(regs_left)
                reg_map[new_map_k] = deref
                regints.add(new_map_k)          #Update regints
                regs_left.append(new_map_k)
            # update allocated_cee_regs
            target_regint = regs_left[0]
            if self.reg_map[target_regint] in self.callee_saved_regs:
                self.allocated_cee_regs.add(target_regint)
            # update spilled variables
            if isinstance(target_regint, Deref):
                spilled_variables.add(v)
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
                # print(color )
                return self.reg_map[loc_regint_map[a]]
            case _:
                return a
            
    def replace_in_instr(self, i: instr, color) -> instr:
        match i:
            # case Instr(cmd, [arg1, arg2]) if cmd in self.instrs_two:
            case Instr(cmd, [arg1, arg2]):
                return Instr(cmd, [self.select_color(arg1, color), self.select_color(arg2, color)])
            # case Instr(cmd, [arg1]) if cmd in self.instrs_one:
            case Instr(cmd, [arg1]):
                return Instr(cmd, [self.select_color(arg1, color)])
            case _:
                return i

    # TODO
    # - save callee allocated list
    # - Minimum allocation number

    def allocate_registers(self, p: X86Program,
                           graph: UndirectedAdjList) -> X86Program:
        color = self.color_graph(graph, self.get_variables(graph))
        body = p.get_body()
        # used callee saved registers
        p.used_callee = set([self.reg_map[s] for s in self.allocated_cee_regs])
        # offset for stack space in reg_map
        offset = 8*len(p.used_callee)
        for key,loc in self.reg_map.items():
            match loc:
                case Deref("rbp", off1):
                    self.reg_map[key] = Deref("rbp", off1 - offset)
        # allocate registers
        for block,instrs in body.items():
            body[block] = [self.replace_in_instr(i, color) for i in instrs]
        return p

    # ############################################################################
    # # Assign Homes
    # ############################################################################

    def assign_homes(self, pseudo_x86: X86Program) -> X86Program:
        graph = self.build_interference(pseudo_x86, self.uncover_live(pseudo_x86))
        # print("Graph")
        # print(graph)
        x86prog = self.allocate_registers(pseudo_x86, graph)
        return x86prog

    # ###########################################################################
    # # Patch Instructions
    # ###########################################################################

    def patch_instructions(self, p: X86Program) -> X86Program:
        x86prog = super().patch_instructions(p)
        return x86prog

    # ###########################################################################
    # # Prelude & Conclusion
    # ###########################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        # Calculate stack_sapce
        # temp1 = align(8S+8C)
        temp1 = math.ceil((8*(self.stack_var_num + len(p.used_callee)))/16)*16
        A = temp1 - 8 * len(p.used_callee)
        p.stack_space = A
        p = super().prelude_and_conclusion(p)
        return p
