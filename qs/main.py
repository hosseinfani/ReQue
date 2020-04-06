import os, sys
sys.path.extend(["./cair"])

from cair.main.recommender import run

def call_cair_run(data_dir):
    dataset_name = 'msmarco'#it is hard code in the library. Do not touch it! :))
    baseline_path = 'cair/'

    cli_cmd  = '' #'python '
    cli_cmd += '{}main/recommender.py '.format(baseline_path)

    cli_cmd += '--dataset_name {} '.format(dataset_name)
    cli_cmd += '--data_dir {} '.format(data_dir)

    cli_cmd += '--max_query_len 20 '
    cli_cmd += '--uncase True '
    cli_cmd += '--num_candidates 0 '
    cli_cmd += '--emsize 300 '
    cli_cmd += '--batch_size 8 '
    cli_cmd += '--test_batch_size 8 '
    cli_cmd += '--num_epochs 100 '
    cli_cmd += '--data_workers 5 '
    cli_cmd += '--valid_metric bleu '
    cli_cmd += '--embed_dir {}data/fasttext/ '.format(baseline_path)
    cli_cmd += '--embedding_file crawl-300d-2M-subword.vec '

    #the models config are in query_expansion\qs\cair\neuroir\hyparam.py
    #hredqs can only be unidirectional, so all other models are in bidirectional mode
    for baseline in ['seq2seq', 'acg', 'hredqs']:
        run((cli_cmd + '--model_dir {}/{} --model_name {} --model_type {} '.format(data_dir, baseline, baseline, baseline)).split())
if __name__=='__main__':
    rankers = ['-bm25', '-bm25 -rm3', '-qld', '-qld -rm3']
    metrics = ['map']
    dbs = ['robust04', 'gov2', 'clueweb09b', 'clueweb12b13']
    for ranker in rankers:
        ranker = ranker.replace('-', '').replace(' ', '.')
        for metric in metrics:
            for db in dbs:
                data_dir = '../ds/qs/{}/topics.{}.{}.{}/'.format(db, db, ranker, metric)
                print('INFO: MAIN: Calling cair for {}'.format(data_dir))
                call_cair_run(data_dir)
