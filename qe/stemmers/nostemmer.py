#!/bin/python
from abstractstemmer import AbstractStemmer
import sys


class NoStemmer(AbstractStemmer):

    def __init__(self, ):
        super(NoStemmer, self).__init__()
        self.basename = 'nostemmer'

    def process(self, words):
        return words


if __name__ == '__main__':
    stemmer = NoStemmer()
    stemmer.stem(sys.argv[1:])
