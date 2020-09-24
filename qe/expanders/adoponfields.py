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
from expanders.relevancefeedback import RelevanceFeedback
from expanders.onfields import QueryExpansionOnFields
from cmn import utils

stop_words = set(stopwords.words('english'))
ps = PorterStemmer()


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

class AdobpQEOnFields(RelevanceFeedback):

    def __init__(self, ranker, prels, anserini, index, corpus,externalindex, externalcorpus,externalprels, replace=False, topn=3, top_n_terms=10,adop=False):
        RelevanceFeedback.__init__(self, ranker, prels, anserini, index, topn=topn)
        self.corpus = corpus
        self.index_reader = pyserini.index.IndexReader(self.index)
        self.top_n_terms=10
        self.adop=adop
        self.externalindex=externalindex
        self.externalcorpus=externalcorpus
        self.externalprels=externalprels

    def get_expanded_query(self, q, args):
        qid=args[0]
        Preferred_expansion=self.avICTF(q)
        if Preferred_expansion =="NoExpansionPreferred":
            output_weighted_q_dic={}
            for terms in q.split():
                output_weighted_q_dic[ps.stem(terms)]=2
            return output_weighted_q_dic
        elif Preferred_expansion =="InternalExpansionPreferred":
            qe = QueryExpansionOnFields(ranker=self.ranker,
                           prels=self.prels,
                           anserini=self.anserini,
                           index=self.index,
                           corpus=self.corpus)

            return(qe.get_expanded_query(q, [qid]))
        elif Preferred_expansion =="ExternalExpansionPreferred":
            qe = QueryExpansionOnFields(ranker=self.ranker,
                           prels=self.externalprels,
                           anserini=self.anserini,
                           index=self.externalindex,
                           corpus=self.externalcorpus,
                           adop=True)
            return(qe.get_expanded_query(q, [qid]))


    def get_model_name(self):
        return super().get_model_name().replace('topn{}'.format(self.topn),
                                                'EX{}.topn{}.{}'.format(self.externalcorpus,self.topn, self.top_n_terms))
                                                
    def avICTF(self,query):
        # Other collections number of total tokens needs to be added if required
        collection_token={'robust04':148000000,
                   'gov2' : 17000000000,
                   'cw09' : 31000000000, 
                   'cw12' : 31000000000}

        index_reader = index.IndexReader(self.externalindex)
        ql=len(query.split())
        sub_result=1
        for term in query.split():
            df, collection_freq = index_reader.get_term_counts(term)
            if collection_freq ==0:
                collection_freq=1

            sub_result= sub_result * (collection_token[self.externalcorpus] / collection_freq)
        sub_result=math.log2(sub_result)
        externalavICTF= (sub_result/ql)
        index_reader = index.IndexReader(self.index)
        sub_result=1
        for term in query.split():
            df, collection_freq = index_reader.get_term_counts(term)
            if collection_freq ==0:
                collection_freq=1
            sub_result= sub_result * (collection_token[self.corpus] / collection_freq)
        sub_result=math.log2(sub_result)
        internalavICTF = (sub_result/ql)
        if internalavICTF < 10 and externalavICTF < 10:
            return "NoExpansionPreferred"
        elif internalavICTF >= externalavICTF:
            return "InternalExpansionPreferred"
        elif externalavICTF > internalavICTF:
            return "ExternalExpansionPreferred"


if __name__ == "__main__":
    qe = QueryExpansionOnFields(ranker='bm25',
                                prels='../ds/qe/gov2/topics.terabyte04.701-750.abstractqueryexpansion.bm25.txt',
                                anserini='../anserini/',
                                index='../anserini/lucene-index.gov2.pos+docvectors+rawdocs',
                                corpus='gov2')

    print(qe.get_model_name())
    print(qe.get_expanded_query('pearl farming', [702]))

    qe = AdobpQEOnFields(ranker='bm25',
                           corpus='robust04',
                           index='/data/anserini/lucene-index.robust04.pos+docvectors+rawdocs',
                           prels='../ds/qe/robust04/topics.robust04.abstractqueryexpansion.bm25.txt',
                           anserini='.../anserini/',
                           externalcorpus='gov2',
                           externalindex='/data/anserini/lucene-index.gov2.pos+docvectors+rawdocs',
                           externalprels='../ds/qe/gov2/topics.terabyte04.701-750.abstractqueryexpansion.bm25.txt')
                           
    print(qe.get_model_name())

    print(qe.get_expanded_query('most dangerous vehicle', [305]))