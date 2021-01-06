import os, sys, re, io
sys.path.extend(['../qe'])

from pyserini.search import SimpleSearcher
from cmn import utils #although it's not used here, this is required!
from expanders.relevancefeedback import RelevanceFeedback

class RM3(RelevanceFeedback):
    def __init__(self, ranker, index, topn=10, topw=10, original_q_w=0.5):
        RelevanceFeedback.__init__(self, ranker=ranker, prels=None, anserini=None, index=index, topn=topn)
        self.topw=topw
        self.searcher = SimpleSearcher(index)
        self.ranker=ranker
        self.original_q_w=original_q_w


    def get_expanded_query(self, q, args=None):
        
        if self.ranker=='bm25':
            self.searcher.set_bm25()
        elif self.ranker=='qld':
            self.searcher.set_qld()

        self.searcher.set_rm3(fb_terms=self.topw, fb_docs=self.topn, original_query_weight=self.original_q_w, rm3_output_query=True)
        
        f = io.BytesIO()
        with utils.stdout_redirector_2_stream(f):
            self.searcher.search(q)
        print('RM3 Log: {0}"'.format(f.getvalue().decode('utf-8')))
        q_= self.parse_rm3_log(f.getvalue().decode('utf-8'))

        # with stdout_redirected(to='rm3.log'):
        #     self.searcher.search(q)
        # rm3_log = open('rm3.log', 'r').read()
        # q_ = self.parse_rm3_log(rm3_log)
        # os.remove("rm3.log")

        return q_

    def get_model_name(self):
        return super().get_model_name().replace('topn{}'.format(self.topn), 'topn{}.{}.{}'.format(self.topn, self.topw, self.original_q_w))

    def parse_rm3_log(self,rm3_log):
        new_q=rm3_log.split('Running new query:')[1]
        new_q_clean=re.findall('\(([^)]+)', new_q)
        new_q_clean=" ".join(new_q_clean)
        return new_q_clean


if __name__ == "__main__":
    qe = RM3(index='../ds/robust04/index-robust04-20191213/' )
    print(qe.get_model_name())
    print(qe.get_expanded_query('International Crime Organization'))
