# ReQue: A Benchmark Workflow and Dataset Collection for Query Refinement

## Getting Started

### Overview
```qe/```: codebase for the query expansion methods (expanders).
```qs/```: codebase for the query suggestion methods (suggesters), including [seq2seq with Attention](https://nlp.stanford.edu/pubs/emnlp15_attn.pdf), [acg](https://arxiv.org/abs/1708.03418), [hred-qs](https://arxiv.org/abs/1507.02221).
```pre/```: source folder for pre-trained models and/or embeddings, including [fasttext](https://fasttext.cc/docs/en/english-vectors.html) and [GloVe](https://nlp.stanford.edu/projects/glove/).
```ds/```: source folder for corpuses, including Robust04, Gov2, ClueWeb09, and ClueWeb12.
```ds/qe/```: target folder for expanders' outputs.
```ds/qs```: target folder for suggesters' outputs.
```anserini/```: source folder for [Anserini](https://github.com/castorini/anserini) library and output indices for the corpuses.


### Prerequisites

**Library**

```
python 3.7
```
```
pandas, scipy, numpy, collections, requests, urllib, subprocess
```
```
networkx, community
```
```
gensim, tagme, bs4, pywsd, nltk [stem, tokenize, corpus]
```
```
anserini
```

**Pre-trained Model/Embedding**

- [fasttext](https://fasttext.cc/docs/en/english-vectors.html)
- [GloVe](https://nlp.stanford.edu/projects/glove/)
- [Joint Embedding of Hierarchical Categories and Entities for Concept Categorization and Dataless Classification](https://www.aclweb.org/anthology/C16-1252/)

**Corpus/Dataset**

- Robust04 [corpus, topics, qrels]
- Gov2 [corpus, topics, qrels]
- ClueWeb09 [corpus, topics, qrels]
- ClueWeb12 [corpus, topics, qrels]
- [Wikipedia Anchor Text](http://downloads.dbpedia.org/2016-10/core-i18n/en/anchor_text_en.ttl.bz2)

### Installing

- [Anserini](https://github.com/castorini/anserini) must be installed for indexing, information retrieval, and evaluation in the ```anserini/``` folder. The documents in the corpuses must be indexed by the following commands.

*Robust04* (already available at [here](https://git.uwaterloo.ca/jimmylin/anserini-indexes/raw/master/index-robust04-20191213.tar.gz))
```
$> anserini/target/appassembler/bin/IndexCollection -collection TrecCollection -input Robust04-Corpus -index lucene-index.robust04.pos+docvectors+rawdocs -generator JsoupGenerator -threads 44 -storePositions -storeDocvectors -storeRawDocs 2>&1 | tee log.robust04.pos+docvectors+rawdocs &
```


*Gov2*
```
$> query_expansion/anserini/target/appassembler/bin/IndexCollection -collection TrecwebCollection -input Gov2-Corpus -index lucene-index.gov2.pos+docvectors+rawdocs -generator JsoupGenerator -threads 44 -storePositions -storeDocvectors -storeRawDocs 2>&1 | tee log.gov2.pos+docvectors+rawdocs &
```

*ClueWeb09-B-Corpus*
```
$> query_expansion/anserini/target/appassembler/bin/IndexCollection -collection ClueWeb09Collection -input ClueWeb09-B-Corpus -index lucene-index.cw09b.pos+docvectors+rawdocs -generator JsoupGenerator -threads 44 -storePositions -storeDocvectors -storeRawDocs 2>&1 | tee  log.cw09b.pos+docvectors+rawdocs &
```

*ClueWeb12-B-Corpus*
```
$> query_expansion/anserini/target/appassembler/bin/IndexCollection -collection ClueWeb12Collection -input ClueWeb12-B-Corpus -index lucene-index.cw12b13.pos+docvectors+rawdocs -generator JsoupGenerator -threads 44 -storePositions -storeDocvectors -storeRawDocs 2>&1 | tee  log.cw12b13.pos+docvectors+rawdocs &
```

## Running
### Query Expansion (qe)
The ```qe/main.py``` accept the corpus name whose queries are to be expanded and evaluated.
```
$> python -u qe/main.py robust04 2>&1 | tee robust04.log &
$> python -u qe/main.py gov2 2>&1 | tee gov2.log &
$> python -u qe/main.py clueweb09b 2>&1 | tee clueweb09b.log &
$> python -u qe/main.py clueweb12b13 2>&1 | tee clueweb12b13.log &
```

### Query Suggestion (qs)
The ```qs/main.py``` accept top-k; k is an positive integer, for considering the top-k golden expanded queries and the name of the corpus. Following commands are for top-5. It benchmark the golden expanded queries for [seq2seq with Attention](https://nlp.stanford.edu/pubs/emnlp15_attn.pdf), [acg](https://arxiv.org/abs/1708.03418), [hred-qs](https://arxiv.org/abs/1507.02221) by using the codebase provided by [Ahmad et al.](https://github.com/wasiahmad/context_attentive_ir).
```
$> python -u qs/main.py 5 robust04 2>&1 | tee robust04.topn5.log &
$> python -u qs/main.py 5 gov2 2>&1 | tee gov2.topn5.log &
$> python -u qs/main.py 5 clueweb09b 2>&1 | tee clueweb09b.topn5.log &
$> python -u qs/main.py 5 clueweb12b13 2>&1 | tee clueweb12b13.topn5.log &
$> python -u qs/main.py 5 all 2>&1 | tee all.topn5.log &
```

## Authors

## License

## Acknowledgments
