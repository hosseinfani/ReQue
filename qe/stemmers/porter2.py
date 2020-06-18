#!/bin/python
from stemmers.abstractstemmer import AbstractStemmer
import stemmers.porter2stemmer as porter2stemmer
import sys


class Porter2Stemmer(AbstractStemmer):

    def __init__(self, ):
        super(Porter2Stemmer, self).__init__()
        self.basename = 'porter2'

    def process(self, words):
        return [porter2stemmer.stem(word) for word in words]


if __name__ == '__main__':
    stemmer = Porter2Stemmer()
    stemmer.stem(sys.argv[1:])
