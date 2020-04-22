#TODO: needs some refactor
import os, enum, os.path
from os import path
import pandas as pd

import sys
sys.path.extend(['../qe'])
from cmn import expander_factory

class AnalysisLevel(enum.Enum):
    PER_FILE = 1
    PER_DATASET = 2
    OVERALL = 3


class QueryExpanderCategory(enum.Enum):
    Stemming_Analysis = 1
    Semantic_Analysis = 2
    Term_Clustering = 3
    Concept_clustering = 4
    Anchor_text = 5
    Wikipedia = 6
    Top_Documents = 7
    Document_Summaries = 8


class ResultAnalyzer:
    rankers = ["bm25", "bm25.rm3", "qld", "qld.rm3"]
    metrics = ["map"]
    dataset_names = ["robust04",
                     #"gov2",
                     "clueweb12b13",
                     "clueweb09b"
                     ]

    pattern = "topics.{original_dataset_name}.{topic_first_index-topic_last_index}.{ranker}.{metric}.dataset.csv"

    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.query_expander_contributions = {}
        # the number of times a technique has generated the best expanded query
        self.query_expander_contributions_best = {}

        self.reset()

    def get_indices_for_dataset(self, dataset):
        indices = dict({
            "robust04": [""],
            #"gov2": [".701-850"],
            "clueweb12b13": [".201-300"],
            "clueweb09b": [".1-200"]
        })
        return indices.get(dataset, None)

    def reset(self):
        self.number_of_improvements = 0
        self.number_of_queries = 0
        self.improvement_count = 0
        self.improvement_sum = 0.0
        if len(self.query_expander_contributions):
            for key in self.query_expander_contributions:
                self.query_expander_contributions[key] = 0
        if len(self.query_expander_contributions_best):
            for key in self.query_expander_contributions_best:
                self.query_expander_contributions_best[key] = 0

    def collect_query_expander_names(self):
        names = expander_factory.get_expanders_names(['-bm25', '-bm25 -rm3', '-qld', '-qld -rm3'])
        for name in names:
            self.add_to_query_expander_names(name)

    def add_to_query_expander_names(self, query_expander_name):
        current_value = self.query_expander_contributions.get(query_expander_name, None)
        if current_value is None:
            self.query_expander_contributions[query_expander_name] = 0
        current_value = self.query_expander_contributions_best.get(query_expander_name, None)
        if current_value is None:
            self.query_expander_contributions_best[query_expander_name] = 0

    def analyze_level(self, level):
        self.level = level
        if self.level == AnalysisLevel.OVERALL:
            output_file_name = self.output_path + os.sep + "overall.stat.csv"
            self.prepare(output_file_name)
            self.output = open(output_file_name, "w")
        for dataset in self.dataset_names:
            self.current_dataset = dataset
            print("DATASET: {}".format(self.current_dataset))
            if self.level == AnalysisLevel.PER_DATASET:
                output_file_name = self.output_path + os.sep + self.current_dataset + os.sep + self.current_dataset + ".stat.csv"
                self.prepare(output_file_name)
                self.output = open(output_file_name, "w")
            for ranker in self.rankers:
                self.current_ranker = ranker
                for metric in self.metrics:
                    self.current_metric = metric
                    csv_file_name = self.pattern
                    csv_file_name = csv_file_name.replace("{original_dataset_name}", self.current_dataset)
                    csv_file_name = csv_file_name.replace("{ranker}", self.current_ranker)
                    csv_file_name = csv_file_name.replace("{metric}", self.current_metric)
                    indices = self.get_indices_for_dataset(self.current_dataset)

                    for index in indices:
                        temp = csv_file_name.replace(".{topic_first_index-topic_last_index}", index)
                        csv_file = self.input_path + os.sep + self.current_dataset + os.sep + temp
                        if self.level == AnalysisLevel.PER_FILE:
                            output_file_name = csv_file.replace(self.input_path, self.output_path).replace(
                                "dataset.csv", "dataset.stat.csv")
                            self.prepare(output_file_name)
                            self.output = open(output_file_name, "w")
                        self.analyze_file(csv_file)
                        if self.level == AnalysisLevel.PER_FILE:
                            self.post_process()

            if self.level == AnalysisLevel.PER_DATASET:
                self.post_process()
        if self.level == AnalysisLevel.OVERALL:
            self.post_process()

    def prepare(self, file):
        try:
            directory = file[0: file.rindex(os.sep)]
            if not path.exists(directory):
                os.makedirs(directory)
        except OSError:
            print("Creation of the directory {} failed".format(directory))

    def post_process(self):
        self.print_results()
        self.output.close()
        self.reset()

    def print_results(self):
        if self.number_of_queries == 0:
            print("No result available")
        else:
            sorted_map = sorted(self.query_expander_contributions.keys())
            for key in sorted_map:
                self.output.write(",{}".format(key))
            self.output.write("\n")
            self.output.write("contributionToAll")
            for key in sorted_map:
                self.output.write(",{}".format(self.query_expander_contributions[key]))

            self.output.write("\n")
            self.output.write("contributionToBest")
            sorted_map = sorted(self.query_expander_contributions_best.keys())
            for key in sorted_map:
                self.output.write(",{}".format(self.query_expander_contributions_best[key]))

            self.output.write("\n\n ")
            self.output.write("AVG_QE_PER_Q, AVG_QE_IMPROVEMENT")
            self.output.write("\n")
            average = self.number_of_improvements * 1.0 / self.number_of_queries
            improvement_average = self.improvement_sum * 1.0 / self.improvement_count
            self.output.write("{},{}".format(round(average, 2), round(improvement_average, 2)))

            self.output.write("\n\n")
            for category in QueryExpanderCategory:
                self.output.write(",{}".format(str(category).replace("QueryExpanderCategory.", "")))
            self.output.write("\n")
            self.output.write("contributionToAll")
            for category in QueryExpanderCategory:
                sum = 0
                for key in sorted_map:
                    if self.belongs(key, category):
                        sum += self.query_expander_contributions[key]
                self.output.write(",{}".format(sum))

            self.output.write("\n")
            self.output.write("contributionToBest")
            total = 0
            for category in QueryExpanderCategory:
                sum = 0
                for key in sorted_map:
                    if self.belongs(key, category):
                        sum += self.query_expander_contributions_best[key]
                total += sum
                self.output.write(",{}".format(sum))

            self.output.write("\n")
            self.output.write("contributionToBest(Percentage)")
            for category in QueryExpanderCategory:
                sum = 0
                for key in sorted_map:
                    if self.belongs(key, category):
                        sum += self.query_expander_contributions_best[key]
                ratio = round(sum * 1.0 / total * 100, 2)
                self.output.write(",{}".format(ratio))

    def belongs(self, query_expander_method, query_expander_category):
        return self.get_category(query_expander_method) == query_expander_category

    def get_category(self, query_expander_method):
        stemming_methods = ["stem.krovetz",
                            "stem.lovins",
                            "stem.paicehusk",
                            "stem.porter",
                            "stem.porter2",
                            "stem.sstemmer",
                            "stem.trunc4",
                            "stem.trunc5",
                            ]
        semantic_methods = ["conceptnet.topn3",
                            "conceptnet.topn3.replace",
                            "glove.topn3",
                            "glove.topn3.replace",
                            "sensedisambiguation",
                            "sensedisambiguation.replace",
                            "thesaurus.topn3",
                            "thesaurus.topn3.replace",
                            "word2vec.topn3",
                            "word2vec.topn3.replace",
                            "wordnet.topn3",
                            "wordnet.topn3.replace"
                            ]
        term_clustering_methods = ["termluster.topn5.3.bm25",
                                   "termluster.topn5.3.bm25.rm3",
                                   "termluster.topn5.3.qld",
                                   "termluster.topn5.3.qld.rm3",
                                   ]
        concept_clustering_methods = ["conceptluster.topn5.3.bm25",
                                      "conceptluster.topn5.3.bm25.rm3",
                                      "conceptluster.topn5.3.qld",
                                      "conceptluster.topn5.3.qld.rm3",
                                      ]
        anchor_text_methods = ["anchor.topn3",
                               "anchor.topn3.replace",
                               ]
        wikipedia_methods = ["wiki.topn3",
                             "wiki.topn3.replace",
                             "tagmee.topn3",
                             "tagmee.topn3.replace",
                             ]
        top_documents_methods = ["relevancefeedback.topn10.bm25",
                                 "relevancefeedback.topn10.bm25.rm3",
                                 "relevancefeedback.topn10.qld",
                                 "relevancefeedback.topn10.qld.rm3",
                                 ]
        document_summaries_methods = ["docluster.topn10.3.bm25",
                                      "docluster.topn10.3.bm25.rm3",
                                      "docluster.topn10.3.qld",
                                      "docluster.topn10.3.qld.rm3",
                                      ]
        if query_expander_method in semantic_methods:
            return QueryExpanderCategory.Semantic_Analysis
        elif query_expander_method in stemming_methods:
            return QueryExpanderCategory.Stemming_Analysis
        elif query_expander_method in term_clustering_methods:
            return QueryExpanderCategory.Term_Clustering
        elif query_expander_method in concept_clustering_methods:
            return QueryExpanderCategory.Concept_clustering
        elif query_expander_method in anchor_text_methods:
            return QueryExpanderCategory.Anchor_text
        elif query_expander_method in wikipedia_methods:
            return QueryExpanderCategory.Wikipedia
        elif query_expander_method in top_documents_methods:
            return QueryExpanderCategory.Top_Documents
        elif query_expander_method in document_summaries_methods:
            return QueryExpanderCategory.Document_Summaries

    def analyze_file(self, csv_file):
        print("processing file {}".format(csv_file))

        if not path.exists(csv_file):
            print("File not found: {}".format(csv_file))
        data_frame = pd.read_csv(csv_file)
        for index, row in data_frame.iterrows():
            original_metric_value = 0 if not row[2] else float(row[2])
            number_of_improvements = int(row[3])
            self.number_of_improvements += number_of_improvements
            self.number_of_queries += 1
            if number_of_improvements > 0:
                for i in range(number_of_improvements):
                    improved_metric_value = float(row[5 + i * 3])
                    if i == 0 and original_metric_value > 0.0:
                        improvement = (improved_metric_value - original_metric_value) * 100.0 / original_metric_value
                        self.improvement_sum += improvement
                        self.improvement_count += 1
                    improved_method_name = row[5 + i * 3 - 1]
                    self.update_map(improved_method_name)
                    if i == 0:
                        self.update_map2(improved_method_name)

    def update_map(self, name):
        current_value = self.query_expander_contributions.get(name, None)
        current_value = int(current_value)
        self.query_expander_contributions[name] = current_value + 1

    def update_map2(self, name):
        current_value = self.query_expander_contributions_best.get(name, None)
        current_value = int(current_value)
        self.query_expander_contributions_best[name] = current_value + 1


def main():
    input_path = "../ds/qe"
    output_path = "../ds/qe/eval"
    analyzer = ResultAnalyzer(input_path, output_path)
    analyzer.collect_query_expander_names()
    for level in AnalysisLevel:
        analyzer.analyze_level(level)


if __name__ == "__main__":
    main()

