#!/bin/python
from stemmers.abstractstemmer import AbstractStemmer
import stemmers.paicehuskstemmer as paicehuskstemmer
import sys


class PaiceHuskStemmer(AbstractStemmer):

    def __init__(self, ):
        super(PaiceHuskStemmer, self).__init__()
        self.basename = 'paicehusk'

    def process(self, words):
        return [paicehuskstemmer.stem(word) for word in words]


if __name__ == '__main__':
    stemmer = PaiceHuskStemmer()
    stemmer.stem(sys.argv[1:])
