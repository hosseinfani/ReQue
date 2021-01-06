import tagme
tagme.GCUBE_TOKEN = "10df41c6-f741-45fc-88dd-9b24b2568a7b"

import os,sys
sys.path.extend(['../qe'])

from expanders.termluster import Termluster
from cmn import utils
class Conceptluster(Termluster):
    def __init__(self, ranker, prels, anserini, index, topn=5, topw=3):
        Termluster.__init__(self, ranker, prels, anserini, index, topn=topn, topw=topw)

    def get_expanded_query(self, q, args):
        qid = args[0]
        list_of_concept_lists = []
        docids = self.get_topn_relevant_docids(qid)
        for docid in docids:
            doc_text = self.get_document(docid)
            concept_list = self.get_concepts(doc_text, score=0.1)
            list_of_concept_lists.append(concept_list)

        G, cluster_dict = self.make_graph_document(list_of_concept_lists, min_edge=10)
        expanded_query = self.expand_query_concept_cluster(q, G, cluster_dict, k_relevant_words=self.topw)
        return expanded_query

    def expand_query_concept_cluster(self, q, G, cluster_dict, k_relevant_words):
        q += ' ' + ' '.join(self.get_concepts(q, 0.1))
        return super().expand_query_term_cluster(q, G, cluster_dict, k_relevant_words)

    def get_document(self, docid):
        command = '\"{}target/appassembler/bin/IndexUtils\" -index \"{}\" -dumpRawDoc \"{}\"'.format(self.anserini, self.index, docid)
        stream = os.popen(command)
        return stream.read()

    def get_concepts(self, text, score):
        concepts = tagme.annotate(text).get_annotations(score)
        return list(set([c.entity_title for c in concepts if c.entity_title not in text]))


if __name__ == "__main__":
    qe = Conceptluster(ranker='bm25',
                   prels='./output/robust04/topics.robust04.abstractqueryexpansion.bm25.txt',
                   anserini='../anserini/',
                   index='../ds/robust04/index-robust04-20191213')

    for i in range(5):
        print(qe.get_model_name())
        print(qe.get_expanded_query('HosseinFani International Crime Organization', [301]))
        print(qe.get_expanded_query('Agoraphobia', [698]))
        print(qe.get_expanded_query('Unsolicited Faxes', [317]))
