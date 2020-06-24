from nltk.corpus import wordnet
import urllib, traceback
from urllib.request import urlopen
from bs4 import BeautifulSoup

import sys
sys.path.extend(['../qe'])

from expanders.abstractqexpander import AbstractQExpander
from cmn import utils

class Thesaurus(AbstractQExpander):
    def __init__(self, replace=False, topn=3):
        AbstractQExpander.__init__(self, replace, topn)

    def get_expanded_query(self, q, args=None):
        pos_dict = {'n': 'noun', 'v': 'verb', 'a': 'adjective', 's': 'satellite adj', 'r': 'adverb'}
        upd_query = utils.get_tokenized_query(q)
        q_ = []
        if not self.replace:
            q_ = [w for w in upd_query]
        for w in upd_query:
            found_flag = False
            if utils.valid(w):
                pos = wordnet.synsets(w)[0].pos() if wordnet.synsets(w) else 'n'
                syn = self.get_synonym(w, pos_dict[pos])
                if not syn and self.replace:
                    q_.append(w)
                else:
                    q_.append(' '.join(syn))

        return ' '.join(q_)


    def get_synonym(self, word, pos="noun"):
        try:
            if pos == "noun":
                response = urlopen('http://www.thesaurus.com/browse/{}/noun'.format(word))
                # print(response)
            elif pos == "verb":
                response = urlopen('http://www.thesaurus.com/browse/{}/verb'.format(word))
            elif pos == "adjective":
                response = urlopen('http://www.thesaurus.com/browse/{}/adjective'.format(word))
            else:
                # raise PosTagError('invalid pos tag: {}, valid POS tags: {{noun,verb,adj}}'.format(pos))
                print('WARNING: Thesaurus: Invalid pos tag: {}'.format(pos))
                return []
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'lxml')
            counter=0
            result = []
            if len(soup.findAll('ul', {'class': "css-1lc0dpe et6tpn80"})) > 0:
                for s in str(soup.findAll('ul',{'class':"css-1lc0dpe et6tpn80"})[0]).split('href'):
                    if counter < self.topn:
                        counter+=1
                        start_index=s.index('>')
                        end_index=s.index('<', start_index + 1)
                        result.append(s[start_index+1:end_index])
            return result
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return []
        except urllib.error.URLError:
            print("No Internet Connection")
            return []
        except:
            print('WARNING: Thesaurus: Exception has been raised!')
            print(traceback.format_exc())
            return []


if __name__ == "__main__":
    qe = Thesaurus()
    print(qe.get_model_name())
    print(qe.get_expanded_query('HosseinFani International Crime Organization quickly'))

    qe = Thesaurus(replace=True)
    print(qe.get_model_name())
    print(qe.get_expanded_query('HosseinFani International Crime Organization'))
