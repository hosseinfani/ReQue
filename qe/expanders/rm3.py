import traceback
import pandas as pd
import sys,re
sys.path.extend(['../qe'])

from pyserini import search
from pyserini.search import SimpleSearcher

from cmn import utils
from expanders.abstractqexpander import AbstractQExpander

from contextlib import contextmanager
import os

# Thanks to the following links, we can capture outputs from external c/java libs
# - https://eli.thegreenplace.net/2015/redirecting-all-kinds-of-stdout-in-python/
# - https://stackoverflow.com/questions/5081657/how-do-i-prevent-a-c-shared-library-to-print-on-stdout-in-python/17954769#17954769
@contextmanager
def stdout_redirected(to=os.devnull):
    '''
    import os

    with stdout_redirected(to=filename):
        print("from Python")
        os.system("echo non-Python applications are also supported")
    '''
    fd = sys.stdout.fileno()

    ##### assert that Python and C stdio write using the same file descriptor
    ####assert libc.fileno(ctypes.c_void_p.in_dll(libc, "stdout")) == fd == 1

    def _redirect_stdout(to):
        sys.stdout.close() # + implicit flush()
        os.dup2(to.fileno(), fd) # fd writes to 'to' file
        sys.stdout = os.fdopen(fd, 'w') # Python writes to fd

    with os.fdopen(os.dup(fd), 'w') as old_stdout:
        with open(to, 'w') as file:
            _redirect_stdout(to=file)
        try:
            yield # allow code to be run with the redirected stdout
        finally:
            _redirect_stdout(to=old_stdout) # restore stdout.
                                            # buffering and flags such as
                                            # CLOEXEC may be different

class RM3(AbstractQExpander):
    def __init__(self, index, ranker='bm25', replace=False, topn=None, fb_docs=10, fb_terms=10, original_q_w=0.5 ):
        AbstractQExpander.__init__(self, replace=False, topn=topn)
        self.fb_docs=fb_docs
        self.fb_terms=fb_terms
        self.searcher = SimpleSearcher(index)
        self.ranker=ranker
        self.original_q_w=original_q_w


    def get_expanded_query(self, q, args=None):
        
        if self.ranker=='bm25':
            self.searcher.set_bm25()
        elif self.ranker=='qld':
            self.searcher.set_qld()

        self.searcher.set_rm3(fb_terms=self.fb_terms, fb_docs=self.fb_docs, original_query_weight=self.original_q_w, rm3_output_query=True)
        
        with stdout_redirected(to='../ds/qe/rm3.log'):
            self.searcher.search(q)

        rm3_log=open('../ds/qe/rm3.log','r').read()
        
        q= self.parse_rm3_log(rm3_log)
        os.remove("../ds/qe/rm3.log")

        return q

    def get_model_name(self):
        return '{}.topn{}.{}.{}.{}'.format(super().get_model_name(), self.fb_docs, self.fb_terms, self.original_q_w,self.ranker)
        #return super().get_model_name()
        #.replace('topn{}'.format(self.topn),
        #                                        'topn{}.ex{}.{}.{}'.format(self.topn,self.ext_corpus, self.ext_w_t, self.ext_w_a))

    def parse_rm3_log(self,rm3_log):
        new_q=rm3_log.split('Running new query:')[1]
        new_q_clean=re.findall('\(([^)]+)', new_q)
        new_q_clean=" ".join(new_q_clean)
        return new_q_clean


if __name__ == "__main__":
    qe = RM3(index='/mnt/sata_disk/negar/ReQue/index_rb04/index-robust04-20191213/' )
    print(qe.get_model_name())
    print(qe.get_expanded_query('International Crime Organization'))
