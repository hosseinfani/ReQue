import sys
sys.path.extend(['../qe'])

from pyserini.search import SimpleSearcher
import traceback, os, subprocess, nltk, string, math
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from collections import Counter
from nltk.corpus import stopwords
from pyserini import analysis, index
import pyserini

from expanders.relevancefeedback import RelevanceFeedback
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

class OnFields(RelevanceFeedback):
    def __init__(self, ranker, prels, anserini, index, w_t, w_a, corpus_size, replace=False, topn=3, topw=10,adap=False):
        RelevanceFeedback.__init__(self, ranker, prels, anserini, index, topn=topn)
        self.index_reader = pyserini.index.IndexReader(self.index)
        self.topw=10
        self.adap=adap
        self.w_t = w_t # weight for title field
        self.w_a = w_a # weight for anchor field
        self.corpus_size=corpus_size #total number of documents in the collection

    def get_expanded_query(self, q, args):
        q=q.translate(str.maketrans('', '', string.punctuation))
        qid=args[0]
        if self.adap == False:
            topn_docs = self.get_topn_relevant_docids(qid)
        elif self.adap == True:
            topn_docs=self.retrieve_and_get_topn_relevant_docids(ps.stem(q.lower()))
        topn_title=''
        topn_body=''
        topn_anchor=''
        for docid in topn_docs:
            raw_doc=self.extract_raw_documents(docid)
            raw_doc=raw_doc.lower()
            raw_doc= ''.join([i if ord(i) < 128 else ' ' for i in raw_doc])

            title=''
            body=raw_doc
            anchor=''
            try:
                title=self.extract_specific_field(raw_doc,'title')
            except:
                # 'title' field do not exist
                pass
            try:
                body=self.extract_specific_field(raw_doc,'body')
                if body =='':
                    body=raw_doc
            except:
                # 'body' field do not exist
                pass
            try:
                anchor=self.extract_specific_field(raw_doc,'anchor')
            except:
                #'anchor' field do not exist
                pass

            topn_title='{} {}'.format(topn_title ,title)
            topn_anchor = '{} {}'.format(topn_anchor,anchor)
            topn_body='{} {}'.format(topn_body,body)
        topn_title=topn_title.translate(str.maketrans('', '', string.punctuation))
        topn_anchor=topn_anchor.translate(str.maketrans('', '', string.punctuation))
        topn_body=topn_body.translate(str.maketrans('', '', string.punctuation))
        all_topn_docs=  '{} {} {}'.format(topn_body, topn_anchor ,topn_title)
        tfx = self.term_weighting(topn_title,topn_anchor,topn_body)
        tfx=dict(sorted(tfx.items(), key=lambda x: x[1])[::-1])
        w_t_dic={}
        c=0
        

        for term in tfx.keys():
            if term.isalnum():

                c=c+1
                collection_freq =1 
                try:
                    df, collection_freq = self.index_reader.get_term_counts(term)
                except:
                    # term do not exist in the collection
                    pass 
                if collection_freq==0 or collection_freq==None:
                    collection_freq=1

                P_n = collection_freq / self.corpus_size
                try:
                    term_weight= tfx[term] * math.log2( (1 + P_n ) / P_n) + math.log2( 1 + P_n)
                    w_t_dic[term]=term_weight
                except:
                    
                    pass


        sorted_term_weights=dict(sorted(w_t_dic.items(), key=lambda x: x[1])[::-1])
        counter=0
        top_n_informative_words={}
        for keys,values in sorted_term_weights.items():
            counter=counter+1
            top_n_informative_words[keys]=values
            if counter>self.topw:
                break

        expanded_term_freq= {}
        for keys,values in top_n_informative_words.items():
            expanded_term_freq[keys]=all_topn_docs.count(keys)

        for keys,values in top_n_informative_words.items():
            part_A = expanded_term_freq[keys] /max(expanded_term_freq.values())
            part_B = top_n_informative_words[keys] / max(top_n_informative_words.values())
            top_n_informative_words[keys]= round(part_A+part_B,3)

        for original_q_term in q.lower().split():
            top_n_informative_words[ps.stem(original_q_term)]=2

        top_n_informative_words=dict(sorted(top_n_informative_words.items(), key=lambda x: x[1])[::-1])
        return str(top_n_informative_words)

    def get_model_name(self):
        return super().get_model_name().replace('topn{}'.format(self.topn),
                                                'topn{}.{}.{}.{}'.format(self.topn, self.topw, self.w_t, self.w_a))

    def write_expanded_queries(self, Qfilename, Q_filename,clean=False):
        return super().write_expanded_queries(Qfilename, Q_filename, clean=False)

    def extract_raw_documents(self,docid):
        index_address=self.index
        anserini_address=self.anserini
        cmd = '\"{}/target/appassembler/bin/IndexUtils\" -index \"{}\" -dumpRawDoc \"{}\"'.format(anserini_address,index_address,docid)
        output = subprocess.check_output(cmd, shell=True)
        return (output.decode('utf-8'))
    
    def extract_specific_field(self,raw_document,field):
        soup = BeautifulSoup(raw_document)    # txt is simply the a string with your XML file
        title_out=''
        body_out=''
        anchor_out=''
        if field=='title':
            try:
                title= soup.find('headline')
                title_out=title.text
            except:
                if title_out=='':
                    try:
                        title = soup.find('title')
                        title_out=title.text
                    except:
                        # document had not 'title'
                        pass

            return title_out

        if field == 'body':
            if '<html>' not in raw_document:
                pageText = soup.findAll(text=True)
                body_out= (' '.join(pageText))
            else:
                bodies=  soup.find_all('body')
                for b in bodies:
                    try:
                        body_out='{} {}'.format(body_out,b.text.strip())
                    except:
                        # no 'body' field in the document
                        pass
            return body_out

        if field=='anchor':
            for link in soup.findAll('a'):
                if link.string != None:
                    anchor_out='{} {}'.format(anchor_out,link.string)
            return anchor_out
    

    def term_weighting(self,topn_title,topn_anchor,topn_body):
        # w_t and w_a is tuned for all the copora ( should be tuned for future corpora as well)

        w_b = 1 
        topn_title=topn_title.translate(str.maketrans('', '', string.punctuation))
        topn_body=topn_body.translate(str.maketrans('', '', string.punctuation))
        topn_anchor=topn_anchor.translate(str.maketrans('', '', string.punctuation))

        title_tokens = word_tokenize(topn_title)
        body_tokens= word_tokenize(topn_body)
        anchor_tokens= word_tokenize(topn_anchor)

        filtered_words_title = [ps.stem(word) for word in title_tokens if word not in stop_words]
        filtered_words_body = [ps.stem(word) for word in body_tokens if word not in stop_words]
        filtered_words_anchor = [ps.stem(word) for word in anchor_tokens if word not in stop_words]

        term_freq_title = dict(Counter(filtered_words_title))
        term_freq_body = dict(Counter(filtered_words_body))
        term_freq_anchor = dict(Counter(filtered_words_anchor))

        term_weights={}
        for term in list(set(filtered_words_title)):
            if term not in term_weights.keys():
                term_weights[term]=0
            term_weights[term]=term_weights[term] + term_freq_title[term] * self.w_t

        for term in list(set(filtered_words_body)):
            if  term_freq_body[term]  :
                if term not in term_weights.keys(): 
                    term_weights[term]=0
                term_weights[term]=term_weights[term] + term_freq_body[term]  * w_b

        for term in list(set(filtered_words_anchor)):
            if term not in term_weights.keys():
                term_weights[term]=0
            term_weights[term]=term_weights[term] + term_freq_anchor[term] * self.w_a

        return term_weights

    def retrieve_and_get_topn_relevant_docids(self, q):
        relevant_documents = []
        searcher = SimpleSearcher(self.index)

        if self.ranker =='bm25':
            searcher.set_bm25()
        elif self.ranker=='qld':
            searcher.set_qld()
        hits = searcher.search(q)
        for i in range(0, self.topn):
            relevant_documents.append(hits[i].docid)
        return relevant_documents


if __name__ == "__main__":
    tuned_weights={'robust04':  {'w_t':2.25 , 'w_a':1 },
                    'gov2':     {'w_t':4 , 'w_a':0.25 },
                    'cw09':     {'w_t': 1, 'w_a': 0},
                    'cw12':     {'w_t': 4, 'w_a': 0}} 

    total_documents_number = { 'robust04':520000 , 
                                'gov2' : 25000000, 
                                'cw09' : 50000000 ,
                                'cw12':  50000000}



    qe = OnFields(ranker='bm25',
                                prels='./output/robust04/topics.robust04.abstractqueryexpansion.bm25.txt',
                                anserini='../anserini/',
                                index='./ds/robust04/lucene-index.robust04.pos+docvectors+rawdocs',
                                corpus='robust04',
                                w_t=tuned_weights['robust04']['w_t'],
                                w_a=tuned_weights['robust04']['w_a'],
                                corpus_size= total_documents_number['robust04'])

    print(qe.get_model_name())
    print(qe.get_expanded_query('Most Dangerous Vehicles', [305]))
    

