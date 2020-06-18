import scipy
from nltk.stem import PorterStemmer
import numpy as np

import sys
sys.path.extend(['../qe'])

from expanders.abstractqexpander import AbstractQExpander
from cmn import utils

class Glove(AbstractQExpander):
    def __init__(self, vectorfile, replace=False, topn=3):
        AbstractQExpander.__init__(self, replace, topn)
        Glove.vectorfile = vectorfile
        Glove.glove = None


    def get_expanded_query(self, q, args=None):
        if not Glove.glove:
            print('INFO: Glove: Loading word vectors in {} ...'.format(Glove.vectorfile))
            Glove.glove = load_glove_model(Glove.vectorfile)

        upd_query = utils.get_tokenized_query(q)
        synonyms = []
        res = []
        if not self.replace:
            res = [w for w in upd_query]
        ps = PorterStemmer()
        for qw in upd_query:
            found_flag = False
            qw_stem = ps.stem(qw)
            if qw.lower() in Glove.glove.keys():
                w = sorted(Glove.glove.keys(), key=lambda word: scipy.spatial.distance.euclidean(Glove.glove[word], Glove.glove[qw]))
                w = w[:self.topn]
                for u in w:
                    u_stem = ps.stem(u)
                    if u_stem != qw_stem:
                        found_flag = True
                        res.append(u)
            if not found_flag and self.replace:
                res.append(qw)
        return ' '.join(res)


def load_glove_model(glove_file):
    with open(glove_file + ".txt", 'r', encoding='utf-8') as f:
        model = {}
        counter=0
        for line in f:
            if counter>0:
                split_line = line.split()
                word = split_line[0]
                embedding = np.array([float(val) for val in split_line[1:]])
                model[word] = embedding
                counter+=1
            else:
                counter+=1
    return model

if __name__ == "__main__":
    qe = Glove('../pre/glove.6B.300d')
    for i in range(5):
        print(qe.get_model_name())
        print(qe.get_expanded_query('HosseinFani International Crime Organization'))
    qe.replace = True
    for i in range(5):
        print(qe.get_model_name())
        print(qe.get_expanded_query('HosseinFani International Crime Organization'))


