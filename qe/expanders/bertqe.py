import sys
sys.path.extend(['../qe'])
sys.path.extend(['../pygaggle'])

import pyserini
from pyserini import index
#from pyserini.search import SimpleSearcher
import subprocess, string
import nltk
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from collections import Counter
from nltk.corpus import stopwords
from pygaggle.rerank.base import Query, Text
from pygaggle.rerank.transformer import MonoT5
from nltk.tokenize import word_tokenize 

from pygaggle.rerank.transformer import MonoBERT
from pygaggle.rerank.base import hits_to_texts

from expanders.relevancefeedback import RelevanceFeedback
from cmn import utils

reranker =  MonoBERT()

#@inproceedings{zheng-etal-2020-bert,
#    title = "{BERT-QE}: {C}ontextualized {Q}uery {E}xpansion for {D}ocument {R}e-ranking",
#    author = "Zheng, Zhi  and Hui, Kai  and  He, Ben  and Han, Xianpei  and  Sun, Le  and Yates, Andrew",
#    booktitle = "Findings of the Association for Computational Linguistics: EMNLP 2020",
#    month = nov,
#    year = "2020",
#    address = "Online",
#    publisher = "Association for Computational Linguistics",
#    url = "https://www.aclweb.org/anthology/2020.findings-emnlp.424",
#    pages = "4718--4728",
#}

class BertQE(RelevanceFeedback):
    def __init__(self, ranker, prels, anserini, index):
        RelevanceFeedback.__init__(self, ranker, prels, anserini, index, topn=10)
        self.index_reader = pyserini.index.IndexReader(self.index)


    def get_expanded_query(self, q, args):
        q=q.translate(str.maketrans('', '', string.punctuation))
        qid=args[0]
        topn_docs = self.get_topn_relevant_docids(qid)
        print()
        topn_text=""
        for docid in topn_docs:
            raw_doc=self.index_reader.doc_raw(docid).lower()
            raw_doc= ''.join([i if ord(i) < 128 else ' ' for i in raw_doc])
            topn_text= topn_text+ ' ' + raw_doc

        chunk_dic_for_bert=[]
        chunks=self.make_chunks(topn_text)
        for i in range(len(chunks)):
            chunk_dic_for_bert.append([i,chunks[i]])

        chunk_scores=self.Bert_Score(q,chunk_dic_for_bert)
        scores=list(chunk_scores.values())
        norm = [(float(i)-min(scores))/(max(scores)-min(scores)) for i in scores]
        normalized_chunks={}
        normalized_chunks[q]=1.5
        for i in range(5):
            normalized_chunks[list(chunk_scores.keys())[i]]=norm[i]
        return str(normalized_chunks)

    def write_expanded_queries(self, Qfilename, Q_filename,clean=False):
        return super().write_expanded_queries(Qfilename, Q_filename, clean=False)

    def make_chunks(self,raw_doc):
        chunks=[]
        terms=raw_doc.split()
        for i in range(0, len(terms),5 ):
            chunk=''
            for j in range(i,i+5):
                if j < (len(terms)-1):
                    chunk=chunk+' '+terms[j]   
            chunks.append(chunk)
        return chunks

    def Bert_Score(self,q,doc_dic_for_bert):
        chunk_scores={}
        query = Query(q)
        texts = [ Text(p[1], {'docid': p[0]}, 0) for p in doc_dic_for_bert] 
        reranked = reranker.rerank(query, texts)
        reranked.sort(key=lambda x: x.score, reverse=True)
        for i in range(0,10):
            chunk_text=reranked[i].text
            word_tokens = word_tokenize(chunk_text) 
            filtered_sentence = [w for w in word_tokens if not w in stop_words] 
            filtered_sentence = (" ").join(filtered_sentence).translate(str.maketrans('', '', string.punctuation))
            chunk_scores[filtered_sentence]=round(reranked[i].score,3)
            #print(f'{i+1:2} {reranked[i].score:.5f} {reranked[i].text}')
        return chunk_scores

if __name__ == "__main__":

    qe = BertQE(ranker='bm25',
                prels='./output/robust04/topics.robust04.abstractqueryexpansion.bm25.txt',
                anserini='../anserini/',
                index='../anserini/lucene-index.robust04.pos+docvectors+rawdocs')
    print(qe.get_model_name())
    print(qe.get_expanded_query('International Organized Crime  ', [305]))
    

