#!/usr/bin/python

'''
Reads parse trees from a treebank (each line contains one parse tree)
Converts that tree into a binary tree (input is not necessarily binary)
'''


from tree import Tree
import sys

for line in sys.stdin:
    line = line.strip()
    t = Tree.parse(line)

    # convert to binary and print
    t.binarize()
    print t