import os
import sys
sys.path.extend(['../qe'])

from expanders.abstractqexpander import AbstractQExpander
class RelevanceFeedback(AbstractQExpander):
    def __init__(self, ranker, prels, anserini, index, topn=10):
        AbstractQExpander.__init__(self, replace=False, topn=topn)
        self.prels = prels
        self.f = None
        self.anserini = anserini
        self.index = index
        self.ranker = ranker

    def get_model_name(self):
        return super().get_model_name() + '.' + self.ranker

    def get_expanded_query(self, q, args):
        qid = args[0]
        selected_words = []
        docids = self.get_topn_relevant_docids(qid)
        for docid in docids:
            tfidf = self.get_tfidf(docid)
            top_word, _ = self.get_top_word(tfidf)
            selected_words.append(top_word)

        query_splited = q.lower().split()
        for word in selected_words:
            if word.lower() not in query_splited:
                query_splited.append(word)

        return ' '.join(query_splited)

    def get_topn_relevant_docids(self, qid):
        relevant_documents = []
        if not self.f:
            self.f = open(self.prels, "r", encoding='utf-8')
        self.f.seek(0)
        i = 0
        for x in self.f:
            x_splited =  x.split()
            try :
                if (int(x_splited[0]) == qid or x_splited[0] == qid):
                    relevant_documents.append(x_splited[2])
                    i = i+1
                    if i >= self.topn:
                        break
            except:
                if ('dbpedia' in self.prels and x_splited[0] == qid):
                    relevant_documents.append(x_splited[2])
                    i = i+1
                    if i >= self.topn:
                        break
        return relevant_documents

    def get_tfidf(self, docid):
        #command = "target/appassembler/bin/IndexUtils -index lucene-index.robust04.pos+docvectors+rawdocs -dumpDocVector FBIS4-40260 -docVectorWeight TF_IDF "
        cli_cmd = '\"{}target/appassembler/bin/IndexUtils\" -index \"{}\" -dumpDocVector \"{}\" -docVectorWeight TF_IDF'.format(self.anserini, self.index, docid)
        stream = os.popen(cli_cmd)
        return stream.read()

    def get_top_word(self, tfidf):
        i = 0
        max = 0
        top_word = ""
        for x in tfidf.split('\n'):
            if not x:
                continue
            x_splited = x.split()
            word = x_splited[0]
            value = int(x_splited[1])
            if value > max:
                top_word = word
                max = value

        return top_word, max


if __name__ == "__main__":
    qe = RelevanceFeedback(ranker='bm25',
                           prels='./output/robust04/topics.robust04.abstractqueryexpansion.bm25.txt',
                           anserini='../anserini/',
                           index='../ds/robust04/index-robust04-20191213')
    for i in range(5):
        print(qe.get_model_name())
        print(qe.get_expanded_query('Agoraphobia', [698]))
