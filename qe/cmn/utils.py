from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import re
from contextlib import contextmanager
import os, sys, threading, io, tempfile

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

def get_ranker_name(ranker):
    return ranker.replace('-', '').replace(' ', '.')

# Thanks to the following links, we can capture outputs from external c/java libs
# - https://eli.thegreenplace.net/2015/redirecting-all-kinds-of-stdout-in-python/
# - https://stackoverflow.com/questions/5081657/how-do-i-prevent-a-c-shared-library-to-print-on-stdout-in-python/17954769#17954769

# libc = ctypes.CDLL(None)
# c_stdout = ctypes.c_void_p.in_dll(libc, 'stdout')
@contextmanager
def stdout_redirector_2_stream(stream):
    # The original fd stdout points to. Usually 1 on POSIX systems.
    original_stdout_fd = sys.stdout.fileno()

    def _redirect_stdout(to_fd):
        """Redirect stdout to the given file descriptor."""
        # Flush the C-level buffer stdout
        # libc.fflush(c_stdout)
        # Flush and close sys.stdout - also closes the file descriptor (fd)
        sys.stdout.close()
        # Make original_stdout_fd point to the same file as to_fd
        os.dup2(to_fd, original_stdout_fd)
        # Create a new sys.stdout that points to the redirected fd
        sys.stdout = io.TextIOWrapper(os.fdopen(original_stdout_fd, 'wb'))

    # Save a copy of the original stdout fd in saved_stdout_fd
    saved_stdout_fd = os.dup(original_stdout_fd)
    try:
        # Create a temporary file and redirect stdout to it
        tfile = tempfile.TemporaryFile(mode='w+b')
        _redirect_stdout(tfile.fileno())
        # Yield to caller, then redirect stdout back to the saved fd
        yield
        _redirect_stdout(saved_stdout_fd)
        # Copy contents of temporary file to the given stream
        tfile.flush()
        tfile.seek(0, io.SEEK_SET)
        stream.write(tfile.read())
    finally:
        tfile.close()
        os.close(saved_stdout_fd)

@contextmanager
def stdout_redirected_2_file(to=os.devnull):
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