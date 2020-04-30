import os, sys, time, random, string, json, numpy, pandas as pd
from collections import OrderedDict
sys.path.extend(["./cair", "./cair/main"])

from cair.main.recommender import run

numpy.random.seed(7881)

def generate_random_string(n=12):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def csv2json(df, output):
    if not os.path.isdir(output):
        os.makedirs(output, exist_ok=True)

    for a in ['acg', 'seq2seq', 'hredqs']:
        if not os.path.isdir('{}{}'.format(output, a)):
            os.mkdir('{}{}'.format(output, a))

    with open('{}dataset.json'.format(output), 'w') as fds, \
            open('{}train.json'.format(output), 'w') as ftrain, \
            open('{}dev.json'.format(output), 'w') as fdev, \
            open('{}test.json'.format(output), 'w') as ftest:
        for idx, row in df.iterrows():
            if pd.isna(row.abstractqueryexpansion):
                continue
            session_queries = []
            qObj = OrderedDict([
                ('id', generate_random_string(12)),
                ('text', row.abstractqueryexpansion),
                ('tokens', row.abstractqueryexpansion.split()),
                ('type', ''),
                ('candidates', [])
            ])
            session_queries.append(qObj)
            # set the expanded query to its original form when there is no best expansion => do not expand the query please! It's good enough :))
            if pd.isna(row['query.1']):
                row['query.1'] = row.abstractqueryexpansion
            q_Obj = OrderedDict([
                ('id', generate_random_string(12)),
                ('text', row['query.1']),
                ('tokens', row['query.1'].split()),
                ('type', ''),
                ('candidates', [])
            ])
            session_queries.append(q_Obj)

            obj = OrderedDict([
                ('session_id', generate_random_string()),
                ('query', session_queries)
            ])
            fds.write(json.dumps(obj) + '\n')

            choice = numpy.random.choice(3, 1, p=[0.7, 0.15, 0.15])[0]
            if choice == 0:
                ftrain.write(json.dumps(obj) + '\n')
            elif choice == 1:
                fdev.write(json.dumps(obj) + '\n')
            else:
                ftest.write(json.dumps(obj) + '\n')

def call_cair_run(data_dir):
    dataset_name = 'msmarco'#it is hard code in the library. Do not touch! :))
    baseline_path = 'cair/'

    cli_cmd  = '' #'python '
    cli_cmd += '{}main/recommender.py '.format(baseline_path)
    cli_cmd += '--dataset_name {} '.format(dataset_name)
    cli_cmd += '--data_dir {} '.format(data_dir)
    cli_cmd += '--max_query_len 1000 '
    cli_cmd += '--uncase True '
    cli_cmd += '--num_candidates 0 '
    cli_cmd += '--early_stop 10000 '
    cli_cmd += '--batch_size 8 '
    cli_cmd += '--test_batch_size 8 '
    cli_cmd += '--data_workers 40 '
    cli_cmd += '--valid_metric bleu '
    cli_cmd += '--emsize 300 '
    cli_cmd += '--embed_dir {}data/fasttext/ '.format(baseline_path)
    cli_cmd += '--embedding_file crawl-300d-2M-subword.vec '

    #the models config are in QueStion\qs\cair\neuroir\hyparam.py
    #only hredqs can be unidirectional! all other models are in bidirectional mode
    df = pd.DataFrame(columns=['model', 'epoch', 'rouge', 'bleu', 'bleu_list', 'exact_match', 'f1', 'elapsed_time'])
    for baseline in ['seq2seq', 'acg', 'hredqs']:
        for epoch in [e for e in range(1, 10)] + [e * 10 for e in range(1, 21)]:
            print(epoch)
            start_time = time.time()
            test_resutls = run((cli_cmd + '--model_dir {}/{} --model_name {}.e{} --model_type {} --num_epochs {}'.format(data_dir, baseline, baseline, epoch, baseline, epoch)).split())
            elapsed_time = time.time() - start_time
            df = df.append({'model': baseline,
                            'epoch': epoch,
                            'rouge': test_resutls['rouge'],
                            'bleu': test_resutls['bleu'],
                            'bleu_list': ','.join([str(b) for b  in test_resutls['bleu_list']]),
                            'exact_match': test_resutls['em'],
                            'f1': test_resutls['f1'],
                            'elapsed_time': elapsed_time},
                           ignore_index=True)
            df.to_csv('{}/results.csv'.format(data_dir, baseline), index=False)

if __name__=='__main__':
    rankers = ['-bm25', '-bm25 -rm3', '-qld', '-qld -rm3']
    metrics = ['map']
    dbs = ['robust04', 'gov2', 'clueweb09b', 'clueweb12b13']
    for db in dbs:
        for ranker in rankers:
            ranker = ranker.replace('-', '').replace(' ', '.')
            for metric in metrics:
                # create the test, develop, and train splits
                df = pd.DataFrame()
                if db == 'robust04':
                    df = pd.read_csv('../ds/qe/{}/topics.robust04.{}.{}.dataset.csv'.format(db, ranker, metric), header=0, usecols=['abstractqueryexpansion', 'query.1'])
                    csv2json(df, '../ds/qs/{}/topics.robust04.{}.{}/'.format(db, ranker, metric))
                if db == 'gov2':
                    df = pd.read_csv('../ds/qe/{}/topics.gov2.701-850.{}.{}.dataset.csv'.format(db, ranker, metric), header=0, usecols=['abstractqueryexpansion', 'query.1'])
                    csv2json(df, '../ds/qs/{}/topics.gov2.{}.{}/'.format(db, ranker, metric))
                if db == 'clueweb09b':
                    df = pd.read_csv('../ds/qe/{}/topics.clueweb09b.1-200.{}.{}.dataset.csv'.format(db, ranker, metric), header=0, usecols=['abstractqueryexpansion', 'query.1'])
                    csv2json(df, '../ds/qs/{}/topics.clueweb09b.{}.{}/'.format(db, ranker, metric))
                if db == 'clueweb12b13':
                    df = pd.read_csv('../ds/qe/{}/topics.clueweb12b13.201-300.{}.{}.dataset.csv'.format(db, ranker, metric), header=0, usecols=['abstractqueryexpansion', 'query.1'])
                    csv2json(df, '../ds/qs/{}/topics.clueweb12b13.{}.{}/'.format(db, ranker, metric))

                data_dir = '../ds/qs/{}/topics.{}.{}.{}/'.format(db, db, ranker, metric)
                print('INFO: MAIN: Calling cair for {}'.format(data_dir))
                call_cair_run(data_dir)
