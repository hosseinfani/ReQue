#!/bin/python
from stemmers.abstractstemmer import AbstractStemmer
import stemmers.lovinsstemmer as lovinsstemmer
import sys


class LovinsStemmer(AbstractStemmer):

    def __init__(self, ):
        super(LovinsStemmer, self).__init__()
        self.basename = 'lovins'

    def process(self, words):
        return [lovinsstemmer.stem(word) for word in words]


if __name__ == '__main__':
    stemmer = LovinsStemmer()
    stemmer.stem(sys.argv[1:])
