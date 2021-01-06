import networkx as nx
from collections import defaultdict
from community import community_louvain
from nltk.stem import PorterStemmer

import sys
sys.path.extend(['../qe'])

from expanders.relevancefeedback import RelevanceFeedback
from cmn import utils
class Termluster(RelevanceFeedback):
    def __init__(self, ranker, prels, anserini, index, topn=5, topw=3):
        RelevanceFeedback.__init__(self, ranker, prels, anserini, index, topn=topn)
        self.topw = topw

    def get_model_name(self):
        return super().get_model_name().replace('topn{}'.format(self.topn),'topn{}.{}'.format(self.topn, self.topw))

    def get_expanded_query(self, q, args):
        qid = args[0]
        list_of_word_lists = []
        docids = self.get_topn_relevant_docids(qid)
        for docid in docids:
            tfidf = self.get_tfidf(docid)
            list_of_word_lists.append(self.get_list_of_words(tfidf, threshold=2))

        G, cluster_dict = self.make_graph_document(list_of_word_lists, min_edge=4)

        # add three relevant words from each cluster for each query word
        expanded_query = self.expand_query_term_cluster(q, G, cluster_dict, k_relevant_words=self.topw)

        return expanded_query

    def make_graph_document(self, list_s, min_edge):
        G = nx.Graph()
        counter = 1
        for s in list_s:
            for i in range(len(s) - 1):
                j = i + 1
                while j < len(s):
                    if (s[i], s[j]) in G.edges():
                        G[s[i]][s[j]]['weight'] += 1
                    elif (s[j], s[i]) in G.edges():
                        G[s[j]][s[i]]['weight'] += 1
                    else:
                        G.add_weighted_edges_from([(s[i], s[j], 1)])
                    j += 1
            counter += 1
        G_TH = self.remove_nodes_from_graph(G, min_edge=min_edge)
        clusters_dict = self.get_the_clusters(G_TH)
        return G, clusters_dict

    def remove_nodes_from_graph(self, G, min_edge):
        G = G.copy()
        for n in G.copy().edges(data=True):
            if n[2]['weight'] < min_edge:
                G.remove_edge(n[0], n[1])
        G.remove_nodes_from(list(nx.isolates(G)))
        return G

    def get_the_clusters(self, G):
        clusters = community_louvain.best_partition(G)
        clusters_dic = defaultdict(list)
        for key, value in clusters.items():
            clusters_dic[value].append(key)
        return clusters_dic

    def expand_query_term_cluster(self, q, G, cluster_dict, k_relevant_words):
        upd_query = utils.get_tokenized_query(q)
        porter = PorterStemmer()
        res = [w for w in upd_query]
        for qw in upd_query:
            counter = 0
            for cluster in cluster_dict.values():
                if qw in cluster or porter.stem(qw) in cluster:
                    list_neighbors = [i for i in cluster if (i != qw and i != porter.stem(qw))]
                    counter += 1
                    break
            if counter == 0:
                continue
            weight_list = []
            for i in list_neighbors:
                weight_list.append((i, G.edges[(qw, i)]['weight'] if (qw, i) in G.edges else (porter.stem(qw), i)))
            final_res = sorted(weight_list, key=lambda x: x[1], reverse=True)[:k_relevant_words]
            for u, v in final_res:
                res.append(u)
        return ' '.join(res)

    def get_list_of_words(self, tfidf, threshold):
        list = []
        for x in tfidf.split('\n'):
            if not x:
                continue
            x_splited = x.split()
            w = x_splited[0]
            value = int(x_splited[1])
            if not (w.isdigit()) and w not in stop_words and len(w) > 2 and value > threshold:
                list.append(x_splited[0])

        return list

if __name__ == "__main__":
    qe = Termluster(ranker='bm25',
                   prels='./output/robust04/topics.robust04.abstractqueryexpansion.bm25.txt',
                   anserini='../anserini/',
                   index='../ds/robust04/index-robust04-20191213')
    for i in range(5):
        print(qe.get_model_name())
        # print(qe.get_expanded_query('HosseinFani International Crime Organization', [301]))
        # print(qe.get_expanded_query('Agoraphobia', [698]))
        print(qe.get_expanded_query('Unsolicited Faxes', [317]))
