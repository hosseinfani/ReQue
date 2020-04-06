#!/bin/python
from stemmers.abstractstemmer import AbstractStemmer
import sys


class SRemovalStemmer(AbstractStemmer):

    def __init__(self, ):
        super(SRemovalStemmer, self).__init__()
        self.basename = 'sstemmer'

    def process(self, words):
        return [self.stem_word(word) for word in words]

    def stem_word(self, word):
        if len(word) > 5 and word[-3:] == 'ies' and word[-4] not in 'ae':
            return word[:-3] + 'y'
        elif len(word) > 4 and word[-2:] == 'es' and word[-3] not in 'aeo':
            return word[:-1]
        elif len(word) > 3 and word[-1] == 's' and word[-2] not in 'us':
            return word[:-1]
        else:
            return word


if __name__ == '__main__':
    stemmer = SRemovalStemmer()
    stemmer.stem(sys.argv[1:])
