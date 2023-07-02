from collections import deque
from graph import transpose, DirectedAdjList
from functools import reduce
from utils import trace
from typing import Set

def analyze_dataflow(G:DirectedAdjList,
                     transfer,
                     bottom:Set,
                     join):
    trans_G = transpose(G)
    mapping = {}
    for v in G.vertices():
        mapping[v] = bottom
    worklist = deque()
    for v in G.vertices():
        worklist.append(v)
    while worklist:
        node = worklist.pop()
        # print(node, trans_G.adjacent(node))
        input = reduce(join, [mapping[v] for v in G.adjacent(node)], bottom)
        output = transfer(node, input)
        if output != mapping[node]:
            mapping[node] = output
            for v in trans_G.adjacent(node):
                worklist.append(v)

