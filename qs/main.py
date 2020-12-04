import os, sys, time, random, string, json, numpy, pandas as pd
from collections import OrderedDict
sys.path.extend(["./cair", "./cair/main"])

from cair.main.recommender import run

numpy.random.seed(7881)

def generate_random_string(n=12):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def csv2json(df, output, topn=1):
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
            qObj = OrderedDict([
                ('id', generate_random_string(12)),
                ('text', row.abstractqueryexpansion),
                ('tokens', row.abstractqueryexpansion.split()),
                ('type', ''),
                ('candidates', [])
            ])
            for i in range(1, topn + 1):
                session_queries = []
                session_queries.append(qObj)
                qcol = 'query.' + str(i)
                if (qcol not in df.columns) or pd.isna(row[qcol]):
                    break
                #check if the query string is a dict (for weighted expanders such as onfields)
                try:
                    row[qcol] = ' '.join(eval(row[qcol]).keys())
                except:
                    pass

                q_Obj = OrderedDict([
                    ('id', generate_random_string(12)),
                    ('text', row[qcol]),
                    ('tokens', row[qcol].split()),
                    ('type', ''),
                    ('candidates', [])
                ])
                session_queries.append(q_Obj)

                obj = OrderedDict([
                    ('session_id', generate_random_string()),
                    ('query', session_queries)
                ])
                print(str(row.qid) + ": " + qObj['text'] + '--' + str(i)+ '--> ' + q_Obj['text']);

                fds.write(json.dumps(obj) + '\n')

                choice = numpy.random.choice(3, 1, p=[0.7, 0.15, 0.15])[0]
                if choice == 0:
                    ftrain.write(json.dumps(obj) + '\n')
                elif choice == 1:
                    fdev.write(json.dumps(obj) + '\n')
                else:
                    ftest.write(json.dumps(obj) + '\n')

def call_cair_run(data_dir, epochs):
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
        for epoch in epochs:
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

# # {CUDA_VISIBLE_DEVICES={zero-base gpu index reverse to the system}} python -u main.py {topn=[1,2,...]} {topics=[robust04, gov2, clueweb09b, clueweb12b13, all]} 2>&1 | tee log &

# # python -u main.py 1 robust04 2>&1 | tee robust04.topn1.log &
# # python -u main.py 1 gov2 2>&1 | tee gov2.topn1.log &
# # python -u main.py 1 clueweb09b 2>&1 | tee clueweb09b.topn1.log &
# # python -u main.py 1 clueweb12b13 2>&1 | tee clueweb12b13.topn1.log &
# # python -u main.py 1 antique 2>&1 | tee antique.topn1.log &
# # python -u main.py 1 dbpedia 2>&1 | tee dbpedia.topn1.log &
# # python -u main.py 1 all 2>&1 | tee all.topn1.log &
# # python -u main.py 5 robust04 2>&1 | tee robust04.topn5.log &
# # python -u main.py 5 gov2 2>&1 | tee gov2.topn5.log &
# # python -u main.py 5 clueweb09b 2>&1 | tee clueweb09b.topn5.log &
# # python -u main.py 5 clueweb12b13 2>&1 | tee clueweb12b13.topn5.log &
# # python -u main.py 5 antique 2>&1 | tee antique.topn5.log &
# # python -u main.py 5 dbpedia 2>&1 | tee dbpedia.topn5.log &
# # python -u main.py 5 all 2>&1 | tee all.topn5.log &
# # python -u main.py 100 robust04 2>&1 | tee robust04.topn100.log &
# # python -u main.py 100 gov2 2>&1 | tee gov2.topn100.log &
# # python -u main.py 100 clueweb09b 2>&1 | tee clueweb09b.topn100.log &
# # python -u main.py 100 clueweb12b13 2>&1 | tee clueweb12b13.topn100.log &
# # python -u main.py 100 antique 2>&1 | tee antique.topn100.log &
# # python -u main.py 100 dbpedia 2>&1 | tee dbpedia.topn100.log &
# # python -u main.py 100 all 2>&1 | tee all.topn100.log &

if __name__=='__main__':
    topn = int(sys.argv[1])
    dbs = sys.argv[2:]
    if not dbs:
        dbs = ['robust04', 'gov2', 'clueweb09b', 'clueweb12b13', 'antique', 'all']
    if not topn:
        topn = 1

    rankers = ['-bm25', '-qld']
    metrics = ['map']

    for db in dbs:
        for ranker in rankers:
            ranker = ranker.replace('-', '').replace(' ', '.')
            for metric in metrics:
                # create the test, develop, and train splits
                if db == 'robust04':
                    df = pd.read_csv('../ds/qe/{}/topics.{}.{}.{}.dataset.csv'.format(db, db, ranker, metric), header=0)
                    csv2json(df, '../ds/qs/{}.topn{}/topics.{}.{}.{}/'.format(db, topn, db, ranker, metric), topn)
                if db == 'gov2':
                    df = pd.read_csv('../ds/qe/{}/topics.{}.701-850.{}.{}.dataset.csv'.format(db, db, ranker, metric), header=0)
                    csv2json(df, '../ds/qs/{}.topn{}/topics.{}.{}.{}/'.format(db, topn, db, ranker, metric), topn)
                if db == 'clueweb09b':
                    df = pd.read_csv('../ds/qe/{}/topics.{}.1-200.{}.{}.dataset.csv'.format(db, db, ranker, metric), header=0)
                    csv2json(df, '../ds/qs/{}.topn{}/topics.{}.{}.{}/'.format(db, topn, db, ranker, metric), topn)
                if db == 'clueweb12b13':
                    df = pd.read_csv('../ds/qe/{}/topics.{}.201-300.{}.{}.dataset.csv'.format(db, db, ranker, metric), header=0)
                    csv2json(df, '../ds/qs/{}.topn{}/topics.{}.{}.{}/'.format(db, topn, db, ranker, metric), topn)
                if db == 'antique':
                    df = pd.read_csv('../ds/qe/{}/topics.{}.{}.{}.dataset.csv'.format(db, db, ranker, metric), header=0)
                    csv2json(df, '../ds/qs/{}.topn{}/topics.{}.{}.{}/'.format(db, topn, db, ranker, metric), topn)
                if db == 'dbpedia':
                    df = pd.read_csv('../ds/qe/{}/topics.{}.{}.{}.dataset.csv'.format(db, db, ranker, metric), header=0)
                    csv2json(df, '../ds/qs/{}.topn{}/topics.{}.{}.{}/'.format(db, topn, db, ranker, metric), topn)

                if db == 'all':
                    df1 = pd.read_csv('../ds/qe/robust04/topics.robust04.{}.{}.dataset.csv'.format(ranker, metric), header=0)
                    df2 = pd.read_csv('../ds/qe/gov2/topics.gov2.701-850.{}.{}.dataset.csv'.format(ranker, metric), header=0)
                    df3 = pd.read_csv('../ds/qe/clueweb09b/topics.clueweb09b.1-200.{}.{}.dataset.csv'.format(ranker, metric), header=0)
                    df4 = pd.read_csv('../ds/qe/clueweb12b13/topics.clueweb12b13.201-300.{}.{}.dataset.csv'.format(ranker, metric), header=0)
                    df5 = pd.read_csv('../ds/qe/antique/topics.antique.{}.{}.dataset.csv'.format(ranker, metric), header=0)
                    df6 = pd.read_csv('../ds/qe/dbpedia/topics.dbpedia.{}.{}.dataset.csv'.format(ranker, metric), header=0)
                    df = pd.concat([df1, df2, df3, df4, df5, df6], ignore_index=True)
                    csv2json(df, '../ds/qs/{}.topn{}/topics.{}.{}.{}/'.format(db, topn, db, ranker, metric), topn)

                data_dir = '../ds/qs/{}.topn{}/topics.{}.{}.{}/'.format(db, topn, db, ranker, metric)
                print('INFO: MAIN: Calling cair for {}'.format(data_dir))
                #call_cair_run(data_dir, epochs=[e for e in range(1, 10)] + [e * 10 for e in range(1, 21)])
                call_cair_run(data_dir, epochs=[100])
