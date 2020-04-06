import gensim
import tagme
tagme.GCUBE_TOKEN = "10df41c6-f741-45fc-88dd-9b24b2568a7b"

import sys, os
sys.path.extend(['../qe'])

# @inproceedings{DBLP:conf/coling/LiZTHIS16,
#   author    = {Yuezhang Li and
#                Ronghuo Zheng and
#                Tian Tian and
#                Zhiting Hu and
#                Rahul Iyer and
#                Katia P. Sycara},
#   editor    = {Nicoletta Calzolari and
#                Yuji Matsumoto and
#                Rashmi Prasad},
#   title     = {Joint Embedding of Hierarchical Categories and Entities for Concept
#                Categorization and Dataless Classification},
#   booktitle = {{COLING} 2016, 26th International Conference on Computational Linguistics,
#                Proceedings of the Conference: Technical Papers, December 11-16, 2016,
#                Osaka, Japan},
#   pages     = {2678--2688},
#   publisher = {{ACL}},
#   year      = {2016},
#   url       = {https://www.aclweb.org/anthology/C16-1252/},
#   timestamp = {Mon, 16 Sep 2019 17:08:53 +0200},
#   biburl    = {https://dblp.org/rec/conf/coling/LiZTHIS16.bib},
#   bibsource = {dblp computer science bibliography, https://dblp.org}
# }

from cmn import utils
from expanders.word2vec import Word2Vec

class Wiki(Word2Vec):
    def __init__(self, vectorfile, topn=3, replace=False):
        Word2Vec.__init__(self, vectorfile, topn=topn, replace=replace)

    def get_concepts(self, text, score):
        concepts = tagme.annotate(text).get_annotations(score)
        res = []
        for ann in concepts:
            res.append(ann.entity_title)
        return res

    def get_expanded_query(self, q, args=None):

        if not Word2Vec.word2vec:
            print('INFO: Word2Vec: Loading word vectors in {} ...'.format(Word2Vec.vectorfile))
            Word2Vec.word2vec = gensim.models.KeyedVectors.load(Word2Vec.vectorfile)

        query_concepts = self.get_concepts(q, 0.1)
        upd_query = utils.get_tokenized_query(q)
        res = []
        if not self.replace:
            res = [w for w in upd_query]
        for c in query_concepts:
            c_lower_e = "e_" + c.replace(" ", "_").lower()
            if c_lower_e in Word2Vec.word2vec.vocab:
                w = Word2Vec.word2vec.most_similar(positive=[c_lower_e], topn=self.topn)
                for u, v in w:
                    if u.startswith("e_"):
                        u = u.replace("e_", "")
                    elif u.startswith("c_"):
                        u = u.replace("c_", "")
                    res.append(u.replace("_", " "))

            res.append(c)
        return ' '.join(res)


if __name__ == "__main__":

    qe = Wiki(vectorfile='../pre/temp_model_Wiki')
    for i in range(5):
        print(qe.get_model_name())
        print(qe.get_expanded_query('HosseinFani actor International Crime Organization'))

    qe.replace = True
    for i in range(5):
        print(qe.get_model_name())
        print(qe.get_expanded_query('HosseinFani actor International Crime Organization'))
