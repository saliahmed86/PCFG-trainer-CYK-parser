# PCFG-trainer-CYK-parser
A small Python program to trains a probabilistic context free grammar using a small subset of parse trees from the Penn Treebank, and a CYK parser that uses that PCFG.

## How to run
First preprocess the tree bank to replace single occurence terminals with "\<unk\>"
```
cat train.trees | python replace_onecounts.py > train.trees.unk 2> train.dict
```

Then binarize the trees in the new tree bank
```
cat train.trees.unk | python binarize.py > train.trees.unk.bin
```

Then learn the PCFG
```
cat train.trees.unk.bin | python learn_pcfg.py > grammar.pcfg.bin
```

Run the CYK parser
```
cat test.txt | python cky.py grammar.pcfg.bin train.dict > test.parsed.new
```

Evaluate the results
```
python evalb.py test.trees test.parsed.new
```

## Evaluation

Precision = 314/371 = 0.846
Recall = 314/385 = 0.816
F-1 score = 0.831