import gensim
from nltk.stem import PorterStemmer

import sys
sys.path.extend(['../qe'])

from expanders.abstractqexpander import AbstractQExpander
from cmn import utils

class Word2Vec(AbstractQExpander):
    def __init__(self, vectorfile, replace=False, topn=3):
        AbstractQExpander.__init__(self, replace, topn)
        Word2Vec.vectorfile = vectorfile
        Word2Vec.word2vec = None

    def get_expanded_query(self, q, args=None):
        if not Word2Vec.word2vec:
            print('INFO: Word2Vec: Loading word vectors in {} ...'.format(Word2Vec.vectorfile))
            Word2Vec.word2vec = gensim.models.KeyedVectors.load_word2vec_format(Word2Vec.vectorfile)

        upd_query = utils.get_tokenized_query(q)
        synonyms = []
        res = []
        if not self.replace:
            res = [w for w in upd_query]
        ps = PorterStemmer()
        for qw in upd_query:
            found_flag = False
            qw_stem = ps.stem(qw)
            if qw in Word2Vec.word2vec.vocab:
                w = Word2Vec.word2vec.most_similar(positive=[qw], topn=self.topn)
                for u,v in w:
                    u_stem=ps.stem(u)
                    if  u_stem!=qw_stem:
                        found_flag = True
                        res.append(u)
            if not found_flag and self.replace:
                res.append(qw)
        return ' '.join(res)

if __name__ == "__main__":
    qe = Word2Vec('../pre/wiki-news-300d-1M.vec')
    for i in range(5):
        print(qe.get_model_name())
        print(qe.get_expanded_query('HosseinFani International Crime Organization'))

    qe.replace = True
    for i in range(5):
        print(qe.get_model_name())
        print(qe.get_expanded_query('HosseinFani International Crime Organization'))
