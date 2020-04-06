#TODO: needs some refactor
import os, enum, os.path
from os import path
import pandas as pd

from cmn import expander_factory

class AnalysisLevel(enum.Enum):
    PER_FILE = 1
    PER_DATASET = 2
    OVERALL = 3


class ResultAnalyzer:
    rankers = ["bm25", "bm25.rm3", "qld", "qld.rm3"]
    metrics = ["map"]
    dataset_names = ["robust04",
                     "gov2",
                     "clueweb12b13",
                     "clueweb09b"
                     ]

    pattern = "topics.{original_dataset_name}.{topic_first_index-topic_last_index}.{ranker}.{metric}.dataset.csv"

    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.query_expander_contributions = {}
        self.reset()

    def get_indices_for_dataset(self, dataset):
        indices = dict({
            "robust04": [""],
            "gov2": [".701-850"],
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

    def collect_query_expander_names(self):
        names = expander_factory.get_expanders_names(['-' + r.replace('.',' -') for r in self.rankers])
        for name in names:
            self.add_to_query_expander_names(name)

    def add_to_query_expander_names(self, query_expander_name):
        current_value = self.query_expander_contributions.get(query_expander_name, None)
        if current_value is None:
            self.query_expander_contributions[query_expander_name] = 0

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
            self.output.write("AVG_QE_PER_Q, AVG_QE_IMPROVEMENT")

            for key in self.query_expander_contributions:
                self.output.write(",{}".format(key))
            self.output.write("\n")
            average = self.number_of_improvements * 1.0 / self.number_of_queries
            improvement_average = self.improvement_sum * 1.0 / self.improvement_count
            self.output.write("{},{}".format(round(average, 2), round(improvement_average, 2)))
            for key in self.query_expander_contributions:
                self.output.write(",{}".format(self.query_expander_contributions[key]))

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

    def update_map(self, name):
        current_value = self.query_expander_contributions.get(name, None)
        current_value = int(current_value)
        self.query_expander_contributions[name] = current_value + 1


def main():
    input_path = "../ds/qe"
    output_path = "../ds/qe/stat"
    analyzer = ResultAnalyzer(input_path, output_path)
    analyzer.collect_query_expander_names()
    for level in AnalysisLevel:
        analyzer.analyze_level(level)


if __name__ == "__main__":
    main()
