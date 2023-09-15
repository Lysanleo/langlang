import math
import pprint
import re
from types import GenericAlias
import compiler
import compiler_register_allocator
from ast import *
from graph import UndirectedAdjList
from utils import *
from x86_ast import *
import x86_ast
from data_type import *

pp = pprint.PrettyPrinter()
class CompilerLtup(compiler_register_allocator.Compiler):


    ############################################################################
    # Expose Allocation
    ############################################################################

    def handle_ltup_expr(self, e:expr) -> expr:
        match e:
            # Trans to the L_alloc
            case Tuple(exprs, Load()):
                # notice that in the eoc alloc has a smaller index than inits
                alloc_name = Name(generate_name("alloc"))
                # inits
                # inits = [(Name(generate_name("init")), exp) for exp in exprs]
                inits = {i:Name(generate_name("init")) for i,_ in enumerate(exprs)}
                # calculate bytes
                bytes = 8 + 8 * len(exprs)
                # condictional allocate call
                cond = Compare(BinOp(GlobalValue("free_ptr"),Add(),Constant(bytes))
                              ,[Lt()]
                              ,[GlobalValue("fromspace_end")])
                body = []
                orelse = [Collect(bytes)]
                conditional_call = If(cond, body, orelse)
                # allocate assign
                alloc_assign = Assign([alloc_name], Allocate(len(exprs), e.has_type))
                # assign pairs
                subscript_assign_pairs = [(Subscript(alloc_name, Constant(i), Store()), init_name) for i,init_name in inits.items()]
                inits_assign_pairs = [(init_name, self.handle_ltup_expr(exprs[i])) for i,init_name in inits.items()]
                # assign statements
                init_assigns = make_assigns(inits_assign_pairs)
                sub_assigns = make_assigns(subscript_assign_pairs)
                # append allocation statements
                cont_stmts:list = init_assigns \
                                + [conditional_call] \
                                + [alloc_assign] \
                                + sub_assigns
                # Completed allocation expression
                new_expr = Begin(cont_stmts, alloc_name)
            case BinOp(lhs_exp, op, rhs_exp):
                new_lhs_exp = self.handle_ltup_expr(lhs_exp)
                new_rhs_exp = self.handle_ltup_expr(rhs_exp)
                new_expr = BinOp(new_lhs_exp, op, new_rhs_exp)
            case UnaryOp(op, rhs_exp):
                new_rhs_exp = self.handle_ltup_expr(rhs_exp)
                new_expr = UnaryOp(op, new_rhs_exp)
            case BoolOp(boolop, [exp1, exp2]):
                new_exp1 = self.handle_ltup_expr(exp1)
                new_exp2 = self.handle_ltup_expr(exp2)
                new_expr = BoolOp(boolop, [new_exp1, new_exp2])
            case IfExp(cond_exp, then_exp, orelse_exp):
                new_cond_exp = self.handle_ltup_expr(cond_exp)
                new_then_exp = self.handle_ltup_expr(then_exp)
                new_orelse_exp = self.handle_ltup_expr(orelse_exp)
                new_expr = IfExp(new_cond_exp, new_then_exp, new_orelse_exp)
            case Compare(lhs_exp, [cmp], [rhs_exp]):
                new_lhs_exp = self.handle_ltup_expr(lhs_exp)
                new_rhs_exp = self.handle_ltup_expr(rhs_exp)
                new_expr = Compare(new_lhs_exp, [cmp], [new_rhs_exp])
            case Subscript(exp, index_expr, ctx):
                new_exp = self.handle_ltup_expr(exp)
                new_index_expr = self.handle_ltup_expr(index_expr)
                new_expr = Subscript(new_exp, new_index_expr, ctx)
            case Call(Name('len'), [exp]):
                new_exp = self.handle_ltup_expr(exp)
                new_expr = Call(Name('len'), [new_exp])
            case _:
                new_expr = e
        return new_expr
    
    def handle_ltup_stmt(self, s:stmt) -> stmt:
        match s:
            case Expr(exp):
                new_stmt = Expr(self.handle_ltup_expr(exp))
            case While(cond_exp, bodystmts, []):
                new_cond_exp = self.handle_ltup_expr(cond_exp)
                new_bodystmts = [self.handle_ltup_stmt(stm) for stm in bodystmts]
                new_stmt = While(new_cond_exp, new_bodystmts, [])
            case If(cond_exp, then_stmts, orelse_stmts):
                new_cond_exp = self.handle_ltup_expr(cond_exp)
                new_then_stmts = [self.handle_ltup_stmt(stm) for stm in then_stmts]
                new_orelse_stmts = [self.handle_ltup_stmt(stm) for stm in orelse_stmts]
                new_stmt = If(new_cond_exp, new_then_stmts, new_orelse_stmts)
            case Assign([lhs_var_exp], rhs_exp):
                new_rhs_exp = self.handle_ltup_expr(rhs_exp)
                new_stmt = Assign([lhs_var_exp], new_rhs_exp)
            case _:
                new_stmt = s
        return new_stmt

    # L_tup -> L_Alloc
    def expose_allocation(self, p:Module) -> Module:
        match p:
            case Module(body):
                new_body = [self.handle_ltup_stmt(s) for s in body]
        return Module(new_body)

    ############################################################################
    # Remove Complex Operands
    ############################################################################

    def rco_exp(self, e: expr, need_atomic: bool) -> tuple[expr, Temporaries]:
        match e:
            case GlobalValue(name):
                new_expr = GlobalValue(name)
                new_bindings = []
            case Begin(body_stmts, ret_expr):
                # -> (new_e, [])
                new_body_stmts_temp = [self.rco_stmt(stm) for stm in body_stmts]
                new_body_stmts = list()
                for stmts in new_body_stmts_temp:
                    if stmts:
                        new_body_stmts = new_body_stmts + stmts
                new_expr = Begin(new_body_stmts, ret_expr)
                new_bindings = []
            case Subscript(exp, idx_expr, Load()):
                new_exp_rcotp = self.rco_exp(exp, True)
                # new_index_expr_rcotp = self.rco_exp(index_expr, True)
                new_expr = Subscript(new_exp_rcotp[0], idx_expr, Load())
                new_bindings = new_exp_rcotp[1]
            case Allocate(length, typ):
                new_expr = e
                new_bindings = []
            case Call(Name('len'), [exp]):
                new_exp_rcotp = self.rco_exp(exp, True)
                new_expr = Call(Name('len'), [new_exp_rcotp[0]])
                new_bindings = new_exp_rcotp[1]
            case _:
                return super().rco_exp(e, need_atomic)
        return self.build_atomic_pair(need_atomic, new_expr, new_bindings)
                
    def rco_stmt(self, s: stmt) -> list[stmt]:
        match s:
            case Assign([Subscript(exp, index_expr, Store())], rhs_exp):
                new_exp_rcotp = self.rco_exp(exp, True)
                # new_index_expr_rcotp = self.rco_exp(index_expr, True)
                new_rhs_exp_rcotp = self.rco_exp(rhs_exp, True)
                new_stmts = [Assign([Subscript(new_exp_rcotp[0], index_expr, Store())], new_rhs_exp_rcotp[0])]
            case Collect(size):
                new_stmts = [s]
            case _:
                return super().rco_stmt(s)
        return new_stmts

    def remove_complex_operands(self, p: Module) -> Module:
        match p:
            case Module(body):
                new_body = []
                new_body_temp = [self.rco_stmt(s) for s in body]
                # print(new_body_temp == [None]) => True
                for stmts in new_body_temp:
                    new_body = new_body + stmts
                # print(new_body)
        return Module(new_body)

    ############################################################################
    # Explicate Control
    ############################################################################

    def explicate_stmt(
        self,
        s:stmt,
        cont:Stmts,
        basic_blocks:BasicBlocks
    ) -> Stmts:
        match s:
            case Collect(size):
                return [s] + (cont if cont else [])
            case _:
                return super().explicate_stmt(s, cont, basic_blocks)

    def explicate_control(self, p:Module) -> CProgram(Dict[Label, Stmts]):
        match p:
            case Module(body):
                return super().explicate_control(p)


    ############################################################################
    # Select Instructions
    ############################################################################

    tup_vars = dict()

    def compute_tuple_tag(self, tup_type:TupleType) -> int:
        # type_args = tup_type.__args__
        # type_str = map(lambda x: str(x), type_args)
        length = len(tup_type.types)
        # prog = re.compile(r"^tuple\[")
        # pt_list = zip(map(lambda x: prog.match(x)!=None, type_str),range(0,length))
        pt_list = zip(map(lambda x: isinstance(x, TupleType), tup_type.types),range(0,length))
        pt_mask = sum(map(lambda pr: 1<<(pr[1]+7) if pr[0] else 0, pt_list))
        return pt_mask + (length << 1) + 1

    def assign_helper(
        self, 
        target: list | str, 
        # idx: int,
        rhs: expr,
        Variable,
        # lhs_tuple_p: bool
    ) -> List[instr]:
        instrs = list()
        match target:
            case [Subscript(Name(var), Constant(i), Store())]:
                instrs.append(Instr('movq', [Variable(var), Reg('r11')]))
                instrs.append(Instr('movq', [self.select_arg(rhs), Deref('r11', 8*(i+1))]))
            # case [Name(var)] if isinstance(rhs, Subscript):
            case [Name(var)]:
                match rhs:
                    case Subscript(Name(rhs_tuple), Constant(i), _):
                        instrs.append(Instr('movq', [Variable(rhs_tuple), Reg('r11')]))
                        instrs.append(Instr('movq', [Deref('r11', 8*(i+1)), Variable(var)]))
                    # RHS is allocate
                    case Allocate(bytes, tup_type):
                        # print(tup_type)
                        # print(isinstance(tup_type, GenericAlias))
                        # print(tup_type.types)
                        # Allocate for tuple
                        instrs.append(Instr('movq', [Global('free_ptr'), Reg('r11')]))
                        instrs.append(Instr('addq', [Immediate(8*(bytes+1)), Global('free_ptr')]))
                        instrs.append(Instr('movq', [Immediate(self.compute_tuple_tag(tup_type)), Deref('r11', 0)]))
                        instrs.append(Instr('movq', [Reg('r11'), Variable(var)]))
                    case Compare(operand1, [Is() as cmp], operand2):
                        cc = self.cmp_helper(cmp)
                        instrs = [Instr("cmpq", [operand2, operand1])]
                        instrs.append(Instr("set"+cc, [ByteReg('al')]))
                        instrs.append(Instr("movzbq", [ByteReg('al'), Variable(var)]))
                        return instrs
                    case GlobalValue(gv):
                        instrs.append(Instr('movq', [Global(gv), Variable(var)]))
                    case _:
                        instrs = super().assign_helper(var, rhs, Variable)
            case _:
                # print(target, rhs)
                instrs = super().assign_helper(target, rhs, Variable)
        return instrs

    # def select_instr(self, e: expr) -> List[instr]:
        # match
        # return super().select_instr(e)

    def select_stmt(self, s:stmt) -> List[instr]:
        instrs = list()
        # print(s)
        match s:
            # Tuple write form
            case Assign([Subscript(Name(var), Constant(i), Store())] as lhs, expr):
                # instrs = self.assign_helper(var, i, expr, Variable, True)
                instrs = self.assign_helper(lhs, expr, Variable)
            case Assign([Name(var)] as lhs, expr):
                instrs = self.assign_helper(lhs, expr, Variable)
            case Expr(Collect(bytes)):
                instrs.append(Instr('movq', [Reg('r15'), Reg('rdi')]))
                instrs.append(Instr('movq', [Immediate(bytes), Reg('rsi')]))
                instrs.append(Callq('collect', 1))
            case Collect(byte_size):
                instrs.append(Instr('movq', [Reg('r15'), Reg('rdi')]))
                instrs.append(Instr('movq', [Immediate(byte_size), Reg('rsi')]))
                instrs.append(Callq("collect", 1))
            case _:
                instrs = super().select_stmt(s)
        return instrs
    
    def select_instructions(self, p: Module | CProgram) -> X86Program:
        # pp.pprint(p.var_types)
        # 保存Tyck得到的类型, 用于计算之后的相干图
        if isinstance(p, CProgram):
            # self.var_types = p.var_types
            self.tup_vars = list({ Variable(var_name):typ  for (var_name, typ) in p.var_types.items() if isinstance(typ, TupleType)}.keys())
            pp.pprint(self.tup_vars)
        return super().select_instructions(p)


    ############################################################################
    # Build Interference
    ############################################################################

    # 为TupleType的Variable以及Call Collecter进行特殊处理
    # Edge TupleType var with every allocatable reg, which is `reg_map.value()`
    def add_interference(
        self,
        live_after,
        blk,
        i, 
        instrs,
        inter_graph 
    ):
        # 在相干图中为TupleType的变量连上每一个可分配的Regs.
        def tup_vars_edge_helper(var:Variable, addeds:list[Variable]):
            if var in self.tup_vars and not (var in addeds):
                # print(instrs[i])
                for r in regs:
                    inter_graph.add_edge(var, r)
                addeds.append(var)
        regs = set(self.reg_map.values())
        added_tup_var = []
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
                    tup_vars_edge_helper(arg1, added_tup_var)
                    tup_vars_edge_helper(arg2, added_tup_var)
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
        self.root_stack_var_num = len(added_tup_var) 

    def build_interference(self, p: X86Program, live_after: Dict[Label, Dict[int, Set[location]]]) -> UndirectedAdjList:
        # pp.pprint(live_after)
        return super().build_interference(p, live_after)
    
    ############################################################################
    # Allocate Registers
    ############################################################################

    root_stack_var_num = 0
    spilled_root_stack_variables = []

    def calculate_spilled_variables(self):
        return self.spilled_stack_variables + self.spilled_root_stack_variables

    # record mapint for each variable corresponding stack location
    def add_spilled_varmapkey(self, variable, varmapkey):
        if not (variable in self.tup_vars):
            self.spilled_stack_variables.append(varmapkey)
        else:
            self.spilled_root_stack_variables.append(varmapkey)

    # allocate :: ... -> new reg-int-allocation map
    def allocate_stack(
        self,
        var:Variable,
        regs_left:list[int],
        reg_map:dict,
        regints:set
    ) -> Dict:
        # TupleType Case
        if var in self.tup_vars:
            # Root Stack Space, n(%r15)代表root stack空间
            # Root Stack 其实在栈上(?), 所以它是向上增长的.
            deref = Deref('r15', self.root_stack_var_num*8) 
            self.root_stack_var_num += 1
        else: 
            # Stack Space, n(%rbp)代表常规栈空间
            self.stack_var_num += 1
            deref = Deref('rbp', self.stack_var_num * (-8))
        new_map_k = self.stack_var_num + self.root_stack_var_num - 1 + len(reg_map)
        reg_map[new_map_k] = deref
        regints.add(new_map_k)
        regs_left.append(new_map_k)
        return reg_map

    # All tuple variables are spilled, Thus
    # 1. root_stack_var_num = length of self.tup_vars
    # 2. 
    def allocate_registers(
        self,
        p: X86Program,
        graph: UndirectedAdjList
    ) -> UndirectedAdjList:
        return super().allocate_registers(p, graph)

    # ############################################################################
    # # Assign Homes
    # ############################################################################

    def assign_homes(self, pseudo_x86: X86Program) -> X86Program:
        return super().assign_homes(pseudo_x86)

    # ###########################################################################
    # # Patch Instructions
    # ###########################################################################

    def patch_instructions(self, p: X86Program) -> X86Program:
        # TODO fix the size calc
        x86prog = super().patch_instructions(p)
        return x86prog
        

    # ###########################################################################
    # # Prelude & Conclusion
    # ###########################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        # Calculate stack_sapce
        match p:
            case X86Program(body):
                main_instrs = []
                conclusion_instrs = []
                stack_pushes = []
                stack_pops = []
                call_initialize = []
                root_stack_inits = []
                root_stack_frees = []

                # Calculate stack space' bytes
                temp1 = math.ceil((8*(self.stack_var_num + len(p.used_callee)))/16)*16
                A = temp1 - 8 * len(p.used_callee)
                p.stack_space = A

                # Calculate root stack space' bytes
                root_stack_space = self.root_stack_var_num * 8
                
                # stack p&p
                temp1 = []
                temp2 = [] 
                for r in p.used_callee:
                    temp1.append(Instr('pushq', [r]))
                    temp2.append(Instr('popq', [r]))
                temp2.reverse()

                stack_pushes.extend(temp1)
                # minus rsp
                stack_pushes.append(Instr('subq', [Immediate(p.stack_space), Reg('rsp')]))

                # root_stack_inits
                # argument heap_size and rootstack_size for calling initialize
                # TODO The argument should determined with number of tuple.
                call_initialize.append(Instr('movq', [Immediate(65536), Reg('rdi')]))
                call_initialize.append(Instr('movq', [Immediate(16), Reg('rsi')]))
                call_initialize.append(Callq("initialize",2))
                root_stack_inits.extend(call_initialize)
                root_stack_inits.append(Instr('movq', [Global("rootstack_begin"), Reg('r15')]))
                # TODO Duplicate inits
                temp3 = set()
                for d in range(0, len(self.spilled_root_stack_variables)):
                    temp3.add(Instr('movq', [Immediate(0), self.reg_map[self.spilled_root_stack_variables[d]]]))
                root_stack_inits.extend(temp3)
                root_stack_inits.append(Instr('movq', [Immediate(0), self.reg_map[self.spilled_root_stack_variables[d]]]))
                root_stack_inits.append(Instr('addq', [Immediate(root_stack_space), Reg('r15')]))

                # main instrs
                main_instrs.append(Instr('pushq', [Reg('rbp')]))
                main_instrs.append(Instr('movq', [Reg('rsp'), Reg('rbp')]))
                main_instrs.extend(stack_pushes)
                main_instrs.extend(root_stack_inits)
                main_instrs.append(Jump("start"))

                # root_stack_frees
                root_stack_frees.append(Instr('subq', [Immediate(root_stack_space), Reg('r15')]))

                # stack frees
                stack_pops.append(Instr('addq', [Immediate(p.stack_space), Reg('rsp')]))
                stack_pops.extend(temp2)

                # conclusion instrs
                conclusion_instrs.extend(root_stack_frees)
                conclusion_instrs.extend(stack_pops)
                conclusion_instrs.append(Instr('popq', [Reg('rbp')]))
                conclusion_instrs.append(Retq())
                
                body['main'] = main_instrs
                body["conclusion"] = conclusion_instrs
        return p 