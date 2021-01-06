import sys
sys.path.extend(['../qe'])
sys.path.extend(['../qe/cmn'])

from expanders.abstractqexpander import AbstractQExpander
from expanders.sensedisambiguation import SenseDisambiguation
from expanders.thesaurus import Thesaurus
from expanders.wordnet import Wordnet
from expanders.conceptnet import Conceptnet
from expanders.word2vec import Word2Vec
from expanders.glove import Glove
from expanders.anchor import Anchor
from expanders.tagmee import Tagmee
from expanders.wiki import Wiki
from expanders.relevancefeedback import RelevanceFeedback
from expanders.docluster import Docluster
from expanders.termluster import Termluster
from expanders.conceptluster import Conceptluster
from expanders.onfields import OnFields
from expanders.adaponfields import AdapOnFields
from expanders.bertqe import BertQE
from expanders.rm3 import RM3

from stemmers.krovetz import KrovetzStemmer
from stemmers.lovins import LovinsStemmer
from stemmers.paicehusk import PaiceHuskStemmer
from stemmers.porter import PorterStemmer
from stemmers.porter2 import Porter2Stemmer
from stemmers.sstemmer import SRemovalStemmer
from stemmers.trunc4 import Trunc4Stemmer
from stemmers.trunc5 import Trunc5Stemmer
from expanders.stem import Stem # Stem expander is the wrapper for all stemmers as an expnader :)

import param
from cmn import utils

#global analysis
def get_nrf_expanders():
    expanders = [AbstractQExpander()]
    if param.ReQue['expanders']['Thesaurus']: expanders.append(Thesaurus())
    if param.ReQue['expanders']['Thesaurus']: expanders.append(Thesaurus(replace=True))
    if param.ReQue['expanders']['Wordnet']: expanders.append(Wordnet())
    if param.ReQue['expanders']['Wordnet']: expanders.append(Wordnet(replace=True))
    if param.ReQue['expanders']['Word2Vec']: expanders.append(Word2Vec('../pre/wiki-news-300d-1M.vec'))
    if param.ReQue['expanders']['Word2Vec']: expanders.append(Word2Vec('../pre/wiki-news-300d-1M.vec', replace=True))
    if param.ReQue['expanders']['Glove']: expanders.append(Glove('../pre/glove.6B.300d'))
    if param.ReQue['expanders']['Glove']: expanders.append(Glove('../pre/glove.6B.300d', replace=True))
    if param.ReQue['expanders']['Anchor']: expanders.append(Anchor(anchorfile='../pre/anchor_text_en.ttl', vectorfile='../pre/wiki-anchor-text-en-ttl-300d.vec'))
    if param.ReQue['expanders']['Anchor']: expanders.append(Anchor(anchorfile='../pre/anchor_text_en.ttl', vectorfile='../pre/wiki-anchor-text-en-ttl-300d.vec', replace=True))
    if param.ReQue['expanders']['Wiki']: expanders.append(Wiki('../pre/temp_model_Wiki'))
    if param.ReQue['expanders']['Wiki']: expanders.append(Wiki('../pre/temp_model_Wiki', replace=True))
    if param.ReQue['expanders']['Tagmee']: expanders.append(Tagmee())
    if param.ReQue['expanders']['Tagmee']: expanders.append(Tagmee(replace=True))
    if param.ReQue['expanders']['SenseDisambiguation']: expanders.append(SenseDisambiguation())
    if param.ReQue['expanders']['SenseDisambiguation']: expanders.append(SenseDisambiguation(replace=True))
    if param.ReQue['expanders']['Conceptnet']: expanders.append(Conceptnet())
    if param.ReQue['expanders']['Conceptnet']: expanders.append(Conceptnet(replace=True))
    if param.ReQue['expanders']['KrovetzStemmer']: expanders.append(Stem(KrovetzStemmer(jarfile='stemmers/kstem-3.4.jar')))
    if param.ReQue['expanders']['LovinsStemmer']: expanders.append(Stem(LovinsStemmer()))
    if param.ReQue['expanders']['PaiceHuskStemmer']: expanders.append(Stem(PaiceHuskStemmer()))
    if param.ReQue['expanders']['PorterStemmer']: expanders.append(Stem(PorterStemmer()))
    if param.ReQue['expanders']['Porter2Stemmer']: expanders.append(Stem(Porter2Stemmer()))
    if param.ReQue['expanders']['SRemovalStemmer']: expanders.append(Stem(SRemovalStemmer()))
    if param.ReQue['expanders']['Trunc4Stemmer']: expanders.append(Stem(Trunc4Stemmer()))
    if param.ReQue['expanders']['Trunc5Stemmer']: expanders.append(Stem(Trunc5Stemmer()))
    # since RF needs index and search output which depends on ir method and topics corpora, we cannot add this here. Instead, we run it individually
    # RF assumes that there exist abstractqueryexpansion files

    return expanders

#local analysis
def get_rf_expanders(rankers, corpus, output, ext_corpus=None):
    expanders = []
    for ranker in rankers:
        ranker_name = utils.get_ranker_name(ranker)
        if param.ReQue['expanders']['RM3']: expanders.append(RM3(ranker=ranker_name, index=param.corpora[corpus]['index']))
        if param.ReQue['expanders']['RelevanceFeedback']: expanders.append(RelevanceFeedback(ranker=ranker_name, prels='{}.abstractqueryexpansion.{}.txt'.format(output, ranker_name), anserini=param.anserini['path'], index=param.corpora[corpus]['index']))
        if param.ReQue['expanders']['Docluster']: expanders.append(Docluster(ranker=ranker_name, prels='{}.abstractqueryexpansion.{}.txt'.format(output, ranker_name), anserini=param.anserini['path'], index=param.corpora[corpus]['index'])),
        if param.ReQue['expanders']['Termluster']: expanders.append(Termluster(ranker=ranker_name, prels='{}.abstractqueryexpansion.{}.txt'.format(output, ranker_name), anserini=param.anserini['path'], index=param.corpora[corpus]['index']))
        if param.ReQue['expanders']['Conceptluster']: expanders.append(Conceptluster(ranker=ranker_name, prels='{}.abstractqueryexpansion.{}.txt'.format(output, ranker_name), anserini=param.anserini['path'], index=param.corpora[corpus]['index']))
        if param.ReQue['expanders']['BertQE']: expanders.append(BertQE(ranker=ranker_name, prels='{}.abstractqueryexpansion.{}.txt'.format(output, ranker_name), index=param.corpora[corpus]['index'], anserini=param.anserini['path']))
        if param.ReQue['expanders']['OnFields']: expanders.append(OnFields(ranker=ranker_name, prels='{}.abstractqueryexpansion.{}.txt'.format(output, ranker_name), anserini=param.anserini['path'], index=param.corpora[corpus]['index'],
                                                                          w_t=param.corpora[corpus]['w_t'],
                                                                          w_a=param.corpora[corpus]['w_a'],
                                                                          corpus_size=param.corpora[corpus]['size']))
        if param.ReQue['expanders']['AdapOnFields']: expanders.append(AdapOnFields(ranker=ranker_name,prels='{}.abstractqueryexpansion.{}.txt'.format(output, ranker_name), anserini=param.anserini['path'], index=param.corpora[corpus]['index'],
                                                                              w_t=param.corpora[corpus]['w_t'],
                                                                              w_a=param.corpora[corpus]['w_a'],
                                                                              corpus_size=param.corpora[corpus]['size'],
                                                                              collection_tokens=param.corpora[corpus]['tokens'],
                                                                              ext_corpus=ext_corpus,
                                                                              ext_index=param.corpora[ext_corpus]['index'],
                                                                              ext_collection_tokens=param.corpora[ext_corpus]['tokens'],
                                                                              ext_w_t=param.corpora[ext_corpus]['w_t'],
                                                                              ext_w_a=param.corpora[ext_corpus]['w_a'],
                                                                              ext_corpus_size=param.corpora[ext_corpus]['size'],
                                                                              adap=True))

    return expanders
