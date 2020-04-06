#!/bin/python
from stemmers.abstractstemmer import AbstractStemmer
import sys


class Trunc5Stemmer(AbstractStemmer):

    def __init__(self, ):
        super(Trunc5Stemmer, self).__init__()
        self.basename = 'trunc5'

    def process(self, words):
        return [self.stem_word(word) for word in words]

    def stem_word(self, word):
        if len(word) > 5:
            return word[:5]
        else:
            return word


if __name__ == '__main__':
    stemmer = Trunc5Stemmer()
    stemmer.stem(sys.argv[1:])
