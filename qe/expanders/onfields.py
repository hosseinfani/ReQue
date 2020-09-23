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

from expanders.abstractqexpander import AbstractQExpander
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

class QueryExpansionOnFields:
    def __init__(self, ranker, prels, anserini, index, corpus,replace=False , top_k_docs=3 , top_n_terms=10):
        self.prels = prels
        self.anserini = anserini
        self.index = index
        self.ranker = ranker
        self.replace = replace
        self.corpus = corpus
        self.index_reader = pyserini.index.IndexReader(self.index)
        self.top_n_terms=10
        self.top_k_docs=3


    def get_topn_relevant_docids(self, qid):
        relevant_documents = []
        self.f = open(self.prels, "r", encoding='utf-8')
        self.f.seek(0)
        i = 0
        for x in self.f:
            x_splited =  x.split()
            if int(x_splited[0]) == qid:
                relevant_documents.append(x_splited[2])
                i = i+1
                if i >= self.top_k_docs:
                    break
        return relevant_documents


    def extract_raw_documents(self,docid):
        index_address=self.index
        anserini_address=self.anserini
        cmd = '{}/target/appassembler/bin/IndexUtils -index {} -dumpRawDoc {}'.format(anserini_address,index_address,docid)
        output = subprocess.check_output(cmd, shell=True)
        return (output.decode('utf-8'))
    
    def extract_specific_field(self,raw_document,field):
        soup = BeautifulSoup(raw_document)    # txt is simply the a string with your XML file
        title_out=''
        body_out=''
        anchor_out=''
        if field=='title':
            if self.corpus=='robust04':
                try:
                    title= soup.find('headline')
                    title_out=title.text
                except:
                    pass
            elif self.corpus =='gov2' or self.corpus=='cw09' or self.corpus=='cw12':
                try:
                    title = soup.find('title')
                    title_out=title.text
                except:
                    pass
            return title_out

        if field == 'body':
            if self.corpus=='robust04':
                pageText = soup.findAll(text=True)
                body_out= (' '.join(pageText))
            elif self.corpus =='gov2' or self.corpus=='cw09' or self.corpus=='cw12':
                bodies=  soup.find_all('body')
                for b in bodies:
                    try:
                        body_out='{} {}'.format(body_out,b.text.strip())
                    except:
                        pass
            return body_out

        if field=='anchor':
            for link in soup.findAll('a'):
                if link.string != None:
                    anchor_out='{} {}'.format(anchor_out,link.string)
            return anchor_out
    
    def term_weighting(self,top_3_title,top_3_anchor,top_3_body):
        # w_t and w_a is tuned for all the copora ( should be tuned for future corpora as well)
        if self.corpus =='robust04':
            w_t=2.25
            w_a=1
        elif self.corpus =='gov2':
            w_t=4
            w_a=0.25
        elif self.corpus =='cw09':
            w_t=1
            w_a=0
        elif self.corpus == 'cw12':
            w_t=4
            w_a=0

        w_b = 1 
        top_3_title=top_3_title.translate(str.maketrans('', '', string.punctuation))
        top_3_body=top_3_body.translate(str.maketrans('', '', string.punctuation))
        top_3_anchor=top_3_anchor.translate(str.maketrans('', '', string.punctuation))

        title_tokens = word_tokenize(top_3_title) 
        body_tokens= word_tokenize(top_3_body) 
        anchor_tokens= word_tokenize(top_3_anchor)

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
            term_weights[term]=term_weights[term] + term_freq_title[term] * w_t

        for term in list(set(filtered_words_body)):
            if  term_freq_body[term]  :
                if term not in term_weights.keys(): 
                    term_weights[term]=0
                term_weights[term]=term_weights[term] + term_freq_body[term]  * w_b

        for term in list(set(filtered_words_anchor)):
            if term not in term_weights.keys():
                term_weights[term]=0
            term_weights[term]=term_weights[term] + term_freq_anchor[term] * w_a

        return term_weights

    def get_expanded_query(self, q, args):
        
        qid=args[0]
        top_3_docs = self.get_topn_relevant_docids(qid)
        top_3_title=''
        top_3_body=''
        top_3_anchor=''
        for docid in top_3_docs:
            raw_doc=self.extract_raw_documents(docid)
            raw_doc=raw_doc.lower()
            raw_doc= ''.join([i if ord(i) < 128 else ' ' for i in raw_doc])

            title=''
            body=raw_doc
            anchor=''
            try:
                title=self.extract_specific_field(raw_doc,'title')
            except:
                pass
            try:
                body=self.extract_specific_field(raw_doc,'body')
            except:
                pass
            try:
                anchor=self.extract_specific_field(raw_doc,'anchor')
            except:
                pass

            top_3_title='{} {}'.format(top_3_title ,title)
            top_3_anchor = '{} {}'.format(top_3_anchor,anchor)
            top_3_body='{} {}'.format(top_3_body,body)
        top_3_title=top_3_title.translate(str.maketrans('', '', string.punctuation))
        top_3_anchor=top_3_anchor.translate(str.maketrans('', '', string.punctuation))
        top_3_body=top_3_body.translate(str.maketrans('', '', string.punctuation))
        all_top_3_docs=  '{} {} {}'.format(top_3_body, top_3_anchor ,top_3_title)
        tfx = self.term_weighting(top_3_title,top_3_anchor,top_3_body)
        tfx=dict(sorted(tfx.items(), key=lambda x: x[1])[::-1])
        w_t_dic={}
        c=0
        if self.corpus =='robust04':
            document_number_in_C=520000
        elif self.corpus =='gov2' :
            document_number_in_C=25000000
        elif self.corpus =='cw09'or self.corpus=='cw12':
            document_number_in_C=50000000

        for term in tfx.keys():
            if term.isalnum():

                c=c+1
                collection_freq =1 
                try:
                    df, collection_freq = self.index_reader.get_term_counts(term)
                except:
                    pass 
                if collection_freq==0 or collection_freq==None:
                    collection_freq=1

                P_n = collection_freq / document_number_in_C
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
            if counter>self.top_n_terms:
                break

        expanded_term_freq= {}
        for keys,values in top_n_informative_words.items():
            expanded_term_freq[keys]=all_top_3_docs.count(keys)

        for keys,values in top_n_informative_words.items():
            part_A = expanded_term_freq[keys] /max(expanded_term_freq.values())
            part_B = top_n_informative_words[keys] / max(top_n_informative_words.values())
            top_n_informative_words[keys]= part_A+part_B

        for original_q_term in q.lower().split():
            top_n_informative_words[ps.stem(original_q_term)]=2

        top_n_informative_words=dict(sorted(top_n_informative_words.items(), key=lambda x: x[1])[::-1])
        return str(top_n_informative_words)

    def get_model_name(self):
        return '{}{}{}{}'.format(self.__class__.__name__.lower(),
                         '.topkdocs{}'.format(self.top_k_docs),
                          '.topnterms{}'.format(self.top_n_terms),
                          '.{}'.format(self.ranker))

    def write_expanded_queries(self, Qfilename, Q_filename):
        model_name = self.get_model_name().lower()
        Q_ = pd.DataFrame()
        with open(Qfilename, 'r') as Qfile:
            with open(Q_filename, 'w') as Q_file:
                print('INFO: MAIN: {}: Expanding queries in {} ...'.format(self.get_model_name(), Qfilename))
                for line in Qfile:
                    if '<num>' in line:
                        qid = int(line[line.index(':') + 1:])
                        Q_file.write(line)
                    elif line[:7] == '<title>':#for robust & gov2
                        q = line[8:].strip()
                        if not q:
                            q = next(Qfile).strip()

                        try:
                            q_ = self.get_expanded_query(q, [qid])
                            q_ = utils.clean(q_)
                        except:
                            print('WARNING: MAIN: {}: Expanding query [{}:{}] failed!'.format(self.get_model_name(), qid, q))
                            print(traceback.format_exc())
                            q_ = q

                        Q_ = Q_.append({model_name: q_}, ignore_index=True)
                        print('INFO: MAIN: {}: {}: {} -> {}'.format(self.get_model_name(), qid, q, q_))
                        Q_file.write('<title> ' + q_ + '\n')

                    elif '<topic' in line:
                        s = line.index('\"') + 1
                        e = line.index('\"', s + 1)
                        qid = int(line[s:e])
                        Q_file.write(line)
                    elif line[2:9] == '<query>':#for clueweb09b & clueweb12b13
                            q = line[9:-9]
                            try:
                                q_ = self.get_expanded_query(q, [qid])
                                q_ = utils.clean(q_)
                            except:
                                print('WARNING: MAIN: {}: Expanding query [{}:{}] failed!'.format(self.get_model_name(), qid, q))
                                print(traceback.format_exc())
                                q_ = q

                            Q_ = Q_.append({model_name: q_}, ignore_index=True)
                            print('INFO: MAIN: {}: {}: {} -> {}'.format(self.get_model_name(), qid, q, q_))
                            Q_file.write('  <query>' + q_ + '</query>' + '\n')
                    else:
                        Q_file.write(line)
        return Q_

    def read_expanded_queries(self, Q_filename):
        model_name = self.get_model_name().lower()
        Q_ = pd.DataFrame(columns=['qid'], dtype=int)
        with open(Q_filename, 'r', encoding='utf-8') as Q_file:
            print('INFO: MAIN: {}: Reading expanded queries in {} ...'.format(self.get_model_name(), Q_filename))
            for line in Q_file:
                q_ = None
                if '<num>' in line:
                    qid = int(line[line.index(':') + 1:])
                elif line[:7] == '<title>':#for robust & gov2
                    q_ = line[8:].strip() + ' '
                elif '<topic' in line:
                    s = line.index('\"') + 1
                    e = line.index('\"', s + 1)
                    qid = int(line[s:e])
                elif line[2:9] == '<query>':  # for clueweb09b & clueweb12b13
                    q_ = line[9:-9] + ' '
                else:
                    continue
                if q_:
                    Q_ = Q_.append({'qid': qid, model_name: q_}, ignore_index=True)
        return Q_.astype({'qid': 'int32'})

if __name__ == "__main__":
    qe = QueryExpansionOnFields(ranker='bm25',
                                prels='../ds/qe/gov2/topics.terabyte04.701-750.abstractqueryexpansion.bm25.txt',
                                anserini='../anserini/',
                                index='../anserini/lucene-index.gov2.pos+docvectors+rawdocs',
                                corpus='gov2')

    print(qe.get_model_name())
    print(qe.get_expanded_query('pearl farming', [702]))

