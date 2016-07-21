#!/usr/bin/env python

'''A Penn Treebank-style tree
   author: Liang Huang <lhuang@isi.edu>
   modified: by Ali Ahmed to add "binarize()", "deBinarize()" and "getProductions()"
'''

import sys
logs = sys.stderr

import gflags as flags
FLAGS=flags.FLAGS

from collections import defaultdict

class Tree(object):

    def __init__(self, label, span, wrd=None, subs=None):

        assert (wrd is None) ^ (subs is None), \
               "bad tree %s %s %s" % (label, wrd, subs)
        self.label = label
        self.span = span
        self.word = wrd
        self.subs = subs
        self._str = None
        self._hash = None

    def is_terminal(self):
        return self.word is not None

    def dostr(self):
        return "(%s %s)" % (self.label, self.word) if self.is_terminal() \
               else "(%s %s)" % (self.label, " ".join(map(str, self.subs)))

    def __str__(self):
        if True or self._str is None:
            self._str = self.dostr()
        return self._str

    __repr__ = __str__

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(str(self))
        return self._hash

    def __eq__(self, other):
        ### CAUTION!
        return str(self) == str(other)

    def span_width(self):
        return self.span[1] - self.span[0]

    __len__ = span_width     

    def arity(self):
        return len(self.subs)

    def labelspan(self):
        return "%s [%d-%d]" % (self.label, self.span[0], self.span[1])

    def spanlabel(self):
        return "[%d-%d]: %s" % (self.span[0], self.span[1], self.label)

    @staticmethod
    def _parse(line, pos=0, wrdidx=0, trunc=True):
        ''' returns a triple:
            ( (pos, wordindex), is_empty, tree)
            The is_empty bool tag is used for eliminating emtpy nodes recursively.
            Note that in preorder traversal, as long as the indices do not advance for empty nodes,
            it is fine for stuff after the empty nodes.
        '''
        ## (TOP (S (ADVP (RB No)) (, ,) (NP (PRP it)) (VP (VBD was) (RB n't) (NP (JJ Black) (NNP Monday))) (. .)))
        assert line[pos]=='(', "tree must starts with a ( ! line=%s, pos=%d, line[pos]=%s" % (line, pos, line[pos])
            
        empty = False
        space = line.find(" ", pos)
        label = line[pos + 1 : space]
        if trunc:
            ## remove the PRDs from NP-PRD
            if label[0] != "-":
                dashpos = label.find("-")            
                if dashpos >= 0:
                    label = label[:dashpos]

                ## also NP=2 coreference (there is NP-2 before)
                dashpos = label.find("=")            
                if dashpos >= 0:
                    label = label[:dashpos]

                ## also ADVP|PRT and PRT|ADVP (terrible!)
                dashpos = label.find("|")            
                if dashpos >= 0:
                    label = label[:dashpos]

            else:
                ## remove traces
                ## CAUTION: emptiness is recursive: (NP (-NONE- *T*-1))
                if label == "-NONE-":
                    empty = True
                
        newpos = space + 1
        newidx = wrdidx
        if line[newpos] == '(':
            ## I am non-terminal
            subtrees = []            
            while line[newpos] != ')':
                if line[newpos] == " ":
                    newpos += 1
                (newpos, newidx), emp, sub = Tree._parse(line, newpos, newidx, trunc)
                if not emp:
                    subtrees.append(sub)
                
            return (newpos + 1, newidx), subtrees==[], \
                   Tree(label, (wrdidx, newidx), subs=subtrees)
        
        else:
            ## terminal
            finalpos = line.find(")", newpos)
            word = line[newpos : finalpos]
            ## n.b.: traces shouldn't adv index!
            return (finalpos + 1, wrdidx + 1 if not empty else wrdidx), \
                   empty, Tree(label, (wrdidx, wrdidx+1), wrd=word)

    @staticmethod
    def parse(line, trunc=False):

        _, is_empty, tree = Tree._parse(line, 0, 0, trunc)

        assert not is_empty, "The whole tree is empty! " + line

        if tree.label != "TOP":
            # create another node
            tree = Tree(label="TOP", span=tree.span, subs=[tree])

        return tree            
        
    def all_label_spans(self):
        '''get a list of all labeled spans for PARSEVAL'''

        if self.is_terminal():
            return []
        
        a = [(self.label, self.span)]
        for sub in self.subs:
            a.extend(sub.all_label_spans())

        return a

    def label_span_counts(self):
        '''return a dict mapping (label, span) -> count '''
        d = defaultdict(int)
        for a in self.all_label_spans():
            d[a] += 1
        return d

    def pp(self, level=0):
        if not self.is_terminal():
            print "%s%s" % ("| " * level, self.labelspan())
            for sub in self.subs:
                sub.pp(level+1)
        else:
            print "%s%s %s" % ("| " * level, self.labelspan(), self.word)

    def height(self, level=0):
        if self.is_terminal():
            return 1
        return max([sub.height() for sub in self.subs]) + 1         


    def binarize(self):
        
        if self.subs is not None:
        
            #get number of children. if more than two, put 2...n in temp node
            if len(self.subs) > 2:
                newLabel = self.label
                if newLabel[-1] != "'":
                    newLabel += "'"
                t2  =  Tree(label=newLabel, span=self.span, subs = self.subs[1:])
                self.subs = [self.subs[0], t2]


            for child in self.subs:
                child.binarize()

    def deBinarize(self):
        '''Assumes that this is a binary tree. if a node has more than 2 children, we MIGHT mess up'''
        
        if self.subs is not None:

            while self.subs[-1].label[-1] == "'":
                rhsNode = self.subs[-1]

                rhsLabel = rhsNode.label
                #print rhsLabel
                if rhsLabel[-1] == "'":  #apostrophe indicates this is a temp node, the result of binarization
                    #take both children of this node
                    #remove it from the list

                    #print "this node requires fixing"
                    self.subs.pop()

                    self.subs.extend(rhsNode.subs)

        if self.subs is not None:
            for child in self.subs:
                child.deBinarize()

            


    def getProductions(self):
        prods = []
        #print "label = ",self.label
        #print "word = ", self.word

        if self.subs is not None:
            if len(self.subs) == 2:
                child1 = self.subs[0]
                child2 = self.subs[1]
                prod = (self.label, "%s %s" % (child1.label,child2.label))
                prods.append( prod )
            elif len(self.subs) == 1:
                prod = (self.label, self.subs[0].label)
                prods.append( prod )
                
            for child in self.subs:
                #print "production = ", self.label , " => ", child.label
                childProds = child.getProductions()
                prods.extend(childProds)

        elif self.word is not None:
            #print "production = ", self.label , " => ", self.word
            prod = (self.label, self.word)
            prods.append( prod )

        return prods
                

            



            
###########################################

## attached code does empty node removal ##

###########################################

if __name__ == "__main__":

    flags.DEFINE_integer("max_len", 400, "maximum sentence length")
    flags.DEFINE_boolean("pp", True, "pretty print")
    flags.DEFINE_boolean("height", False, "output the height of each tree")
#    flags.DEFINE_boolean("wordtags", False, "output word/tag sequence")
#    flags.DEFINE_boolean("words", False, "output word sequence")
    flags.DEFINE_boolean("clean", False, "clean up functional tags and empty nodes")
    
    argv = FLAGS(sys.argv)

    for i, line in enumerate(sys.stdin):
        t = Tree.parse(line.strip(), trunc=FLAGS.clean)
        t.binarize()
        if len(t) <= FLAGS.max_len:
            if FLAGS.pp:
                t.pp()
                print t
            elif FLAGS.height:
                print "%d\t%d" % (len(t), t.height())
            else:
                print t


        t.deBinarize()
        if len(t) <= FLAGS.max_len:
            if FLAGS.pp:
                t.pp()
                print t
            elif FLAGS.height:
                print "%d\t%d" % (len(t), t.height())
            else:
                print t


