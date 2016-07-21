'''
Reads the entire tree bank and replaces terminals that occur once
with the symbol "<unk>"

Author: Ali Ahmed
'''


import sys
from collections import defaultdict 
import re

freq = defaultdict(int)
lines = []
#sample tree "(TOP (SQ (VBZ Does) (NP (DT this) (NN flight)) (VP (VB serve) (NP (NN dinner)))))"
unis = []
multis = []

def main():
    for line in sys.stdin:
        line = line.strip()
        lines.append(line)
        
        terminals = re.findall(r'(?:([A-z]+)\))', line)
        for token in terminals:
            freq[token] += 1
    
    unis = [k for k,v in freq.iteritems() if v == 1]
    multis = [k for k,v in freq.iteritems() if v > 1]
    
    regexs = {}
    for word in unis:
        regexs[word] = re.compile("\\b"+word+"\\b")
    
    newlines = []
    for line in lines:
        for word in unis:
            rr = regexs[word]
            line = rr.sub("<unk>" , line)
        print line
            
    for word in multis:
        sys.stderr.write( word + "\n")
    
    
    
if __name__ == "__main__":
    main()