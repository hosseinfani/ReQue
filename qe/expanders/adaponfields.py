import sys
sys.path.extend(['../qe'])

import traceback, os, subprocess, nltk, string, math
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from collections import Counter
from nltk.corpus import stopwords
from pyserini import analysis, index
import pyserini
from pyserini.search import SimpleSearcher
from pyserini import analysis, index

from expanders.onfields import OnFields
from cmn import utils

# @article{DBLP:journals/ipm/HeO07,
#   author    = {Ben He and
#                Iadh Ounis},
#   title     = {Combining fields for query expansion and adaptive query expansion},
#   journal   = {Inf. Process. Manag.},
#   volume    = {43},
#   number    = {5},
#   pages     = {1294--1307},
#   year      = {2007},
#   url       = {https://doi.org/10.1016/j.ipm.2006.11.002},
#   doi       = {10.1016/j.ipm.2006.11.002},
#   timestamp = {Fri, 21 Feb 2020 13:11:30 +0100},
#   biburl    = {https://dblp.org/rec/journals/ipm/HeO07.bib},
#   bibsource = {dblp computer science bibliography, https://dblp.org}
# }

class AdapOnFields(OnFields):

    def __init__(self, ranker, prels, anserini, index, w_t, w_a,corpus_size, collection_tokens,  
                 ext_index, ext_corpus, ext_collection_tokens, ext_w_t, ext_w_a, ext_corpus_size,
                 replace=False, topn=3, topw=10, adap=False):
        OnFields.__init__(self, ranker, prels, anserini, index, w_t, w_a,corpus_size, topn=topn, replace=replace, topw=topw, adap=adap)

        self.collection_tokens = collection_tokens  # number of tokens in the collection

        self.ext_index=ext_index
        self.ext_corpus=ext_corpus
        self.ext_collection_tokens=ext_collection_tokens # number of tokens in the external collection
        self.ext_w_t=ext_w_t
        self.ext_w_a=ext_w_a
        self.ext_corpus_size=ext_corpus_size


    def get_expanded_query(self, q, args):
        qid=args[0]
        Preferred_expansion=self.avICTF(q)
        if Preferred_expansion =="NoExpansionPreferred":
            output_weighted_q_dic={}
            for terms in q.split():
                output_weighted_q_dic[ps.stem(terms)]=2
            return output_weighted_q_dic
        
        elif Preferred_expansion =="InternalExpansionPreferred":
            return(super().get_expanded_query(q, [qid]))
        
        elif Preferred_expansion =="ExternalExpansionPreferred":
            self.adap = True
            self.prels = None#when adap is True, no need for prels since it does the retrieval again!
            self.index = self.ext_index
            self.corpus = self.ext_corpus
            self.w_t = self.ext_w_t
            self.w_a = self.ext_w_a
            self.corpus_size = self.ext_corpus_size
            
            return(super().get_expanded_query(q, [qid]))

    def get_model_name(self):
        return super().get_model_name().replace('topn{}'.format(self.topn),
                                                'topn{}.ex{}.{}.{}'.format(self.topn,self.ext_corpus, self.ext_w_t, self.ext_w_a))

    def write_expanded_queries(self, Qfilename, Q_filename,clean=False):
        return super().write_expanded_queries(Qfilename, Q_filename, clean=False)

    def avICTF(self,query):
        index_reader = index.IndexReader(self.ext_index)
        ql=len(query.split())
        sub_result=1
        for term in query.split():
            try:
                df, collection_freq = index_reader.get_term_counts(ps.stem(term.lower()))
            except:
                collection_freq=1
                df=1

            if isinstance(collection_freq,int)==False:
                collection_freq=1
                df=1

            try:
                sub_result= sub_result * (self.ext_collection_tokens / collection_freq)
            except:
                sub_result= sub_result * self.ext_collection_tokens
        sub_result=math.log2(sub_result)
        externalavICTF= (sub_result/ql)
        index_reader = index.IndexReader(self.index)
        sub_result=1
        for term in query.split():
            try:
                df, collection_freq = index_reader.get_term_counts(ps.stem(term.lower()))
            except:
                collection_freq=1
                df=1
            if  isinstance(collection_freq,int)==False:
                df=1
                collection_freq=1
            try:
                sub_result= sub_result * (self.ext_collection_tokens / collection_freq)
            except:
                sub_result= sub_result * self.ext_collection_tokens
        sub_result=math.log2(sub_result)
        internalavICTF = (sub_result/ql)
        if internalavICTF < 10 and externalavICTF < 10:
            return "NoExpansionPreferred"
        elif internalavICTF >= externalavICTF:
            return "InternalExpansionPreferred"
        elif externalavICTF > internalavICTF:
            return "ExternalExpansionPreferred"


if __name__ == "__main__":
    number_of_tokens_in_collections={'robust04':148000000,
                   'gov2' : 17000000000,
                   'cw09' : 31000000000, 
                   'cw12' : 31000000000}

    tuned_weights={'robust04':  {'w_t':2.25 , 'w_a':1 },
                    'gov2':     {'w_t':4 , 'w_a':0.25 },
                    'cw09':     {'w_t': 1, 'w_a': 0},
                    'cw12':     {'w_t': 4, 'w_a': 0}} 

    total_documents_number = { 'robust04':520000 , 
                                'gov2' : 25000000, 
                                'cw09' : 50000000 ,
                                'cw12':  50000000}

    qe = AdapOnFields(ranker='bm25',
                      corpus='robust04',
                      index='../anserini/lucene-index.robust04.pos+docvectors+rawdocs',
                      prels='./output/robust04/topics.robust04.abstractqueryexpansion.bm25.txt',
                      anserini='../anserini/',
                      w_t=tuned_weights['robust04']['w_t'],
                      w_a=tuned_weights['robust04']['w_a'],
                      corpus_size=total_documents_number['robust04'],
                      collection_tokens=number_of_tokens_in_collections['robust04'],
                      ext_corpus='gov2',
                      ext_index='../anserini/lucene-index.gov2.pos+docvectors+rawdocs',
                      ext_prels='./output/gov2/topics.terabyte04.701-750.abstractqueryexpansion.bm25.txt',
                      ext_collection_tokens = number_of_tokens_in_collections['gov2'],
                      ext_corpus_size=total_documents_number['gov2'],
                      ext_w_t= tuned_weights['gov2']['w_t'],
                      ext_w_a= tuned_weights['gov2']['w_a'],
                           )
                           
    print(qe.get_model_name())

    print(qe.get_expanded_query('most dangerous vehicle', [305]))
