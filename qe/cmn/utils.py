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


def insert_row(df, idx, row):
    import pandas as pd
    df1 = df[0:idx]
    df2 = df[idx:]
    df1.loc[idx] = row
    df = pd.concat([df1, df2])
    df.index = [*range(df.shape[0])]
    return df
