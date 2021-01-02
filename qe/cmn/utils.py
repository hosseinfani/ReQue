from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import re
from contextlib import contextmanager
import os, sys

stop_words = set(stopwords.words('english'))
l = ['.', ',', '!', '?', ';', 'a', 'an', '(', ')', "'", '_', '-', '<', '>', 'if', '/', '[', ']', '&nbsp;']
stop_words.update(l)

ps = PorterStemmer()

def get_tokenized_query(q):
    word_tokens = word_tokenize(q)
    q_ = [w.lower() for w in word_tokens if w.lower() not in stop_words]
    return q_

def valid(word):
    """
    Check if input is null or contains only spaces or numbers or special characters
    """
    temp = re.sub(r'[^A-Za-z ]', ' ', word)
    temp = re.sub(r"\s+", " ", temp)
    temp = temp.strip()
    if temp != "":
        return True
    return False

def clean(str):
    result = [0] * len(str)
    for i in range(len(str)):
        ch = str[i]
        if ch.isalpha():
            result[i] = ch
        else:
            result[i] = ' '
    return ''.join(result)

def insert_row(df, idx, row):
    import pandas as pd
    df1 = df[0:idx]
    df2 = df[idx:]
    df1.loc[idx] = row
    df = pd.concat([df1, df2])
    df.index = [*range(df.shape[0])]
    return df

def get_raw_query(topicreader,Q_filename):
    q_file=open(Q_filename,'r').readlines()
    raw_queries={}
    if topicreader=='Trec':
        for line in q_file:
            if '<title>' in line :
                raw_queries[qid]=line.split('<title>')[1].rstrip().lower()
            elif '<num>' in line:
                qid=line.split(':')[1].rstrip()
                
    elif topicreader=='Webxml':
        for line in q_file:
            if '<query>' in line:
                raw_queries[qid]=line.split('<query>')[1].rstrip().lower().split('</query>')[0]
            elif '<topic number' in line:
                qid=line.split('<topic number="')[1].split('"')[0]
    elif topicreader=='TsvInt' or topicreader=='TsvString':
        for line in q_file:
            qid=line.split('\t')[0]
            raw_queries[qid]=line.split('\t')[1].rstrip().lower()
    return raw_queries

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