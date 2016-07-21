'''
Implements a CYK parser
Implementation based on some pseduocode from http://www.usna.edu/Users/cs/nchamber/courses/nlp/f12/labs/cky-pseudo.html

Author: Ali Ahmed
'''


from __future__ import division
import sys
from collections import defaultdict
import re
import itertools
from tree import Tree


class CKYSolver:
    def __init__(self, text):
        self.nonTerms = set()            #set of non terminals
        self.allProds = set()            #set of all productions
        self.P = defaultdict(float)      #probabilities of productions
        self.score = defaultdict(float)  #n^2|G| matrix to store DP results
        self.backPointers = {}           #to back track
        self.terminals = {}              #maps best non terminal to terminal ("word")
        self.text = text.split()       	 #the list of words
        self.origText = list(self.text)  #list of words, not mutated, to replace "unk" later

        #if we know the list of words that occur multiple times, then replace single occurrences with "<unk>"
        #but keep track of words that we replace, so that final tree has original words
        if len(sys.argv) >= 3:
            trainDict = open(sys.argv[2])
            multiWords = [word.strip() for word in trainDict.readlines()]

            for i,word in enumerate(self.text):
                if word not in multiWords:
                    self.text[i] = "<unk>"

        self.n = len(self.text)



    def addUnary(self,begin, end):
        '''
        Adds unary productions A -> B. These need to be handled differently, since the algo splits B,C in A->BC
        '''
        for A in self.nonTerms:
            for B in self.nonTerms:
                if (A,B) in self.allProds:
                    prob = self.P[(A,B)] * self.score[(begin,end,B)]
        
                    if prob > self.score[(begin,end,A)]:
                        self.score[(begin, end, A)] = prob
                        self.backPointers[(begin, end, A)] = (B,)
        

    def backtrack(self, n):
        '''
        Inits the backtracking process. Calls _backtrack, then deBinarizes tree and returns it.
        Seeds the backtrack process by looking for "TOP" that spans the entire tree
        '''
        if (0,n,'TOP') not in self.backPointers:
            #print "NONE"
            return None

        t = self._backtrack((0,n,'TOP'))

        t.deBinarize()
        return t


    def _backtrack(self, next):
        '''
        Recursive function for backtracking. 
        Next is a triple (low,high,label). "Low" and "high" are bounds that correspond to the span of the tree rooted at "label" (X)
        Next maps to (split, left non terminal (L), right nonTerminal (R)) through the dictionary backPointers
        Essentially, for X -> LR, the map tells us L and R and also the split location.
        '''

        low = next[0]
        high = next[1]
        label = next[2]

        # If this doesn't map to anything, then the search has ended, and it should map to a terminal
        # create a tree node and return the terminal
        if next not in self.backPointers:
            if next in self.terminals:
        
                word = self.origText[next[0]]
                t = Tree(label=label, subs = None, wrd=word, span=(low, high))
        
            return t
        
        #branches is of the form (split_location, Left nonterm, Right nonterm)
        branches = self.backPointers[next]

        #backtracking Unary productions A->B is different. Next maps to (B,)
        #so provide the same low and high for B and send it off to next prodction 
        if len(branches) == 1:
            next = (low, high, branches[0])

            t1 = self._backtrack(next)
            t = Tree(label=label, subs = [t1], wrd=None, span=t1.span)
            return t

        #spans for L,R in X->LR are such that L gets the entire left side, so low to split, and R gets split to high
        elif len(next) == 3:
            (split, left, right) = branches
            next1 = (low, split, left)
            next2 = (split, high, right)

            t1 = self._backtrack(next1)    #left side    
            t2 = self._backtrack(next2) #right side

            #this is the span of X, not L or R. Need it for the tree
            spanLow = t1.span[0]
            spanHigh = t2.span[1]
            t = Tree(label=label, subs = [t1,t2], wrd=None, span=(spanLow, spanHigh))
            return t



    def compute(self):
        '''
        Implements CYK algorithm, while handling all productions of the form A -> w_i,  A -> B C,  A -> B
        Then uses backtrack function to find the best tree, and prints it
        '''
        # first get list stuff
        # read grammars from arg[1]. Parse each line p -> q # prob
        #collection productions, probabilites and non terminals
        for line in open(sys.argv[1]):
            data = re.split(r"\-\>|\#", line.strip())
            
            p = data[0].strip()
            q = data[1].strip()
            prob = float(data[2].strip())
            self.nonTerms.add(p)
            self.allProds.add( (p,q) )
            self.P[(p,q)] = prob
            
        
        #for no real reason, just for printing (not needed anymore)
        self.nonTerms = sorted(list(self.nonTerms))

        #artifact of moving going from handling one sentence to making class for multiple
        n = self.n
        
        #first map pre terminals X -> w_i
        for ii in range(0,n):
            begin = ii
            end = ii + 1

            for A in self.nonTerms:
                word = self.text[begin]

                if (A,word) in self.allProds:
                    self.score[(begin,end,A)] = self.P[(A, word)]

                    # this maps terminals for backtracking
                    self.terminals[(begin,end,A)] = word


            self.addUnary(begin,end)

        #Actual CYK algorithm
        for span in range(2,n+1):
            for begin in range(0,n-span+1):
                end = begin + span
                for split in range(begin+1,end):

                    for A,X in self.allProds:
                        # X is a pair of prodcutions, A -> X where X = L R
                        rhs = X.split()
                        if len(rhs) == 2:
                            B = rhs[0].strip()
                            C = rhs[1].strip()

                            #compute probability of tree rooted at A at begin,end if left, right are B and C resp.
                            prob = self.score[(begin,split,B)] * self.score[(split, end, C)] * self.P[(A, X)]

                            if prob > self.score[(begin, end,  A)]:
                                self.score[(begin, end, A)] = prob
                                self.backPointers[(begin, end, A)] = (split, B, C)


                self.addUnary(begin,end)

        #finished DP algo, now back track and find best tree
        t = self.backtrack(len(self.text))
        if t is not None:
            print t
        else:
            print "NONE"
        



if __name__ == "__main__":
    
    for line in sys.stdin:
        s = CKYSolver(line.strip())
        s.compute()
