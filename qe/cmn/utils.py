from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

stop_words = set(stopwords.words('english'))
l = ['.', ',', '!', '?', ';', 'a', 'an', '(', ')', "'", '_', '-', '<', '>', 'if', '/', '[', ']', '&nbsp;']
stop_words.update(l)

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

    return raw_queries

def convert_onfield_query_format(line):
    line=line.replace("{'",'{"')
    line=line.replace(" '",' "')
    line=line.replace("':",'":')
    line=line.replace("\\","")
    return line


