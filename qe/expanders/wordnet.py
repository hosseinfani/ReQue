from nltk.corpus import wordnet
from nltk.stem import PorterStemmer

import sys
sys.path.extend(['../qe'])

from expanders.abstractqexpander import AbstractQExpander
from cmn import utils

class Wordnet(AbstractQExpander):
    def __init__(self, replace=False, topn=3):
        AbstractQExpander.__init__(self, replace, topn)

    def get_expanded_query(self, q, args=None):
        upd_query = utils.get_tokenized_query(q)
        ps = PorterStemmer()
        synonyms =[]
        res = []
        if not self.replace:
            res=[w for w in upd_query]
        for w in upd_query:
            found_flag = False
            w_stem=ps.stem(w)
            for syn in wordnet.synsets(w):
                for l in syn.lemmas():
                    synonyms.append(l.name())
            synonyms=list(set(synonyms))
            synonyms=synonyms[:self.topn]
            for s in synonyms:
                s_stem=ps.stem(s)
                if  s_stem!=w_stem:
                    found_flag = True
                    res.append(s)
                synonyms=[]

            if not found_flag and self.replace:
                res.append(w)
        return ' '.join(res)

if __name__ == "__main__":
    qe = Wordnet()
    print(qe.get_model_name())
    print(qe.get_expanded_query('HosseinFani International Crime Organization'))

    qe = Wordnet(replace=True)
    print(qe.get_model_name())
    print(qe.get_expanded_query('HosseinFani International Crime Organization'))
