#!/bin/python
from stemmers.abstractstemmer import AbstractStemmer
import sys


class Trunc4Stemmer(AbstractStemmer):

    def __init__(self, ):
        super(Trunc4Stemmer, self).__init__()
        self.basename = 'trunc4'

    def process(self, words):
        return [self.stem_word(word) for word in words]

    def stem_word(self, word):
        if len(word) > 4:
            return word[:4]
        else:
            return word


if __name__ == '__main__':
    stemmer = Trunc4Stemmer()
    stemmer.stem(sys.argv[1:])
