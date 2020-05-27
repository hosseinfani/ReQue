import gensim
from gensim.models.callbacks import CallbackAny2Vec
from gensim.models import KeyedVectors
# from rdflib import Graph

from nltk.stem import PorterStemmer
ps = PorterStemmer()

import sys, os
sys.path.extend(['../qe'])

from expanders.word2vec import Word2Vec
# The anchor texts dataset:
# https://wiki.dbpedia.org/downloads-2016-10
# http://downloads.dbpedia.org/2016-10/core-i18n/en/anchor_text_en.ttl.bz2

class Anchor(Word2Vec):
    def __init__(self, anchorfile, vectorfile, topn=3, replace=False):
        Word2Vec.__init__(self, vectorfile, topn=topn, replace=replace)
        Anchor.anchorfile = anchorfile

    def train(self):

        class AnchorIter:
            def __init__(self, anchorfile):
                self.anchorfile = anchorfile
            def __iter__(self):
                for i, line in enumerate(open(self.anchorfile, encoding='utf-8')):
                    if (i % 10000 == 0 and i > 0):
                        print('INFO: ANCHOR: {} anchors have been read ...'.format(i))
                    s = line.find('> "')
                    e = line.find('"@en', s)
                    if s < 1:
                        continue
                    anchor_text = line[s + 3:e]
                    yield [ps.stem(w) for w in anchor_text.lower().split(' ')]

        class EpochLogger(CallbackAny2Vec):
            def __init__(self, epoch_count):
                self.epoch = 1
                self.epoch_count = epoch_count
            def on_epoch_begin(self, model):
                print("Epoch {}/{} ...".format(self.epoch, self.epoch_count))
                self.epoch += 1
        anchors = AnchorIter(Anchor.anchorfile)
        anchors = [anchor for anchor in AnchorIter(Anchor.anchorfile)]#all in memory at once
        model = gensim.models.Word2Vec(anchors, size=300, sg=1, window=2, iter=100, workers=40, min_count=0, callbacks=[EpochLogger(100)])
        model.wv.save(Anchor.vectorfile)

    def get_expanded_query(self, q, args=None):
        if not Word2Vec.word2vec:
            if not os.path.exists(Anchor.vectorfile):
                print('INFO: ANCHOR: Pretrained anchor vector file {} does not exist! Training has been started ...'.format(Anchor.vectorfile))
                self.train()
            print('INFO: ANCHOR: Loading anchor vectors in {} ...'.format(Anchor.vectorfile))
            Word2Vec.word2vec = gensim.models.KeyedVectors.load(Anchor.vectorfile, mmap='r')

        return super().get_expanded_query(q)

if __name__ == "__main__":
    qe = Anchor(anchorfile='../pre/anchor_text_en.ttl', vectorfile='../pre/wiki-anchor-text-en-ttl-300d-100iter.vec')
    for i in range(5):
        print(qe.get_model_name())
        print(qe.get_expanded_query('HosseinFani actor International Crime Organization'))

    qe.replace = True
    for i in range(5):
        print(qe.get_model_name())
        print(qe.get_expanded_query('HosseinFani actor International Crime Organization'))
