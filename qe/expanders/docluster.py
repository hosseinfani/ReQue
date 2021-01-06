import networkx as nx
from networkx.algorithms import community
import math

import sys
sys.path.extend(['../qe'])

from expanders.relevancefeedback import RelevanceFeedback
class Docluster(RelevanceFeedback):
    def __init__(self, ranker, prels, anserini, index, topn=10, topw=3):
        RelevanceFeedback.__init__(self, ranker, prels, anserini, index, topn=topn)
        self.topw = topw

    def get_model_name(self):
        return super().get_model_name().replace('topn{}'.format(self.topn),'topn{}.{}'.format(self.topn, self.topw))

    def getsim(self, tfidf1, tfidf2):
        words_doc_id_1 = []
        values_doc_id_1 = []

        words_doc_id_2 = []
        values_doc_id_2 = []

        for x in tfidf1.split('\n'):
            if not x:
                continue
            x_splited = x.split()
            words_doc_id_1.append(x_splited[0])
            values_doc_id_1.append(int(x_splited[1]))

        for x in tfidf2.split('\n'):
            if not x:
                continue
            x_splited = x.split()
            words_doc_id_2.append(x_splited[0])
            values_doc_id_2.append(int(x_splited[1]))

        sum_docs_1_2 = 0
        i = 0
        for word in words_doc_id_1:
            try:
                index = words_doc_id_2.index(word)
            except ValueError:
                index = -1
            if index != -1:
                sum_docs_1_2 = sum_docs_1_2 + values_doc_id_1[i] * values_doc_id_2[index]
            i = i + 1

        sum_doc_1 = 0
        for j in range(len(values_doc_id_1)):
            sum_doc_1 = sum_doc_1 + (values_doc_id_1[j] * values_doc_id_1[j])

        sum_doc_2 = 0
        for j in range(len(values_doc_id_2)):
            sum_doc_2 = sum_doc_2 + (values_doc_id_2[j] * values_doc_id_2[j])

        if sum_doc_1 == 0 or sum_doc_2 == 0:
            return 0

        result = sum_docs_1_2 / (math.sqrt(sum_doc_1) * math.sqrt(sum_doc_2))

        return result

    def get_expanded_query(self, q, args):
        qid = args[0]
        selected_words = []
        docids = self.get_topn_relevant_docids(qid)
        tfidfs = []
        for docid in docids:
            tfidfs.append(self.get_tfidf(docid))

        G = nx.Graph()
        for i in range(len(docids)):
            G.add_node(docids[i])
            for j in range(i + 1, len(docids) - 1):
                sim = self.getsim(tfidfs[i], tfidfs[j])
                if sim > 0.5:
                    G.add_weighted_edges_from([(docids[i], docids[j], sim)])
        comp = community.girvan_newman(G)
        partitions = tuple(sorted(c) for c in next(comp))
        for partition in partitions:
            if len(partition) > 1:
                pairlist = []
                for p in partition:
                    pairlist.append(self.get_top_word(tfidf=tfidfs[docids.index(p)]))

                top_k = self.get_top_k(pairlist, self.topw)
                for (word, value) in top_k:
                    selected_words.append(word)

        query_splited = q.lower().split()
        for word in selected_words:
            if word.lower() not in query_splited:
                query_splited.append(word)

        return ' '.join(query_splited)

    def get_top_k(self, pairlist, k):
        output = []
        from_index = 0
        for j in range(min(len(pairlist), k)):
            max_value = 0
            max_index = 0
            max_word = ""
            for i in range(from_index, len(pairlist)):
                (word, value) = pairlist[i]
                if value > max_value:
                    max_value = value
                    max_word = word
                    max_index = i
            output.append((max_word, max_value))
            temp = pairlist[from_index]
            pairlist[from_index] = pairlist[max_index]
            pairlist[max_index] = temp
            from_index = from_index + 1
        return output

if __name__ == "__main__":
    qe = Docluster(ranker='bm25',
                   prels='./output/robust04/topics.robust04.abstractqueryexpansion.bm25.txt',
                   anserini='../anserini/',
                   index='../ds/robust04/index-robust04-20191213')
    for i in range(5):
        print(qe.get_model_name())
        # print(qe.get_expanded_query('HosseinFani International Crime Organization', [301]))
        # print(qe.get_expanded_query('Agoraphobia', [698]))
        print(qe.get_expanded_query('Unsolicited Faxes', [317]))
