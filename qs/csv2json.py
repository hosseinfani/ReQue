import random, string, json, numpy, os
import pandas as pd
from collections import OrderedDict

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
            if pd.isna(row.zbest_expanded_query):
                row.zbest_expanded_query = row.abstractqueryexpansion
            q_Obj = OrderedDict([
                ('id', generate_random_string(12)),
                ('text', row.zbest_expanded_query),
                ('tokens', row.zbest_expanded_query.split()),
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

if __name__=='__main__':
    rankers = ['-bm25', '-bm25 -rm3', '-qld', '-qld -rm3']
    metrics = ['map']
    dbs = ['robust04', 'gov2', 'clueweb09b', 'clueweb12b13']
    for ranker in rankers:
        ranker = ranker.replace('-', '').replace(' ', '.')
        for metric in metrics:
            for db in dbs:
                df = pd.DataFrame()
                if db == 'robust04':
                    df = pd.read_csv('../ds/qe/{}/topics.robust04.{}.{}.dataset.csv'.format(db, ranker, metric), header=0, usecols=['abstractqueryexpansion', 'zbest_expanded_query'])
                    csv2json(df,'../ds/qs/{}/topics.robust04.{}.{}/'.format(db, ranker, metric))
                if db == 'gov2':
                    for r in ['terabyte04.701-750', 'terabyte05.751-800', 'terabyte06.801-850']:
                        df = df.append(pd.read_csv('../ds/qe/{}/topics.{}.{}.{}.dataset.csv'.format(db, r, ranker, metric), header=0, usecols=['abstractqueryexpansion', 'zbest_expanded_query']), ignore_index=True)
                    csv2json(df,'../ds/qs/{}/topics.gov2.{}.{}/'.format(db, ranker, metric))
                if db == 'clueweb09b':
                    for r in ['1-50', '51-100', '101-150', '151-200']:
                        df = df.append(pd.read_csv('../ds/qe/{}/topics.web.{}.{}.{}.dataset.csv'.format(db, r, ranker, metric), header=0, usecols=['abstractqueryexpansion', 'zbest_expanded_query']), ignore_index=True)
                    csv2json(df,'../ds/qs/{}/topics.clueweb09b.{}.{}/'.format(db, ranker, metric))
                if db == 'clueweb12b13':
                    for r in ['201-250', '251-300']:
                        df = df.append(pd.read_csv('../ds/qe/{}/topics.web.{}.{}.{}.dataset.csv'.format(db, r, ranker, metric), header=0,usecols=['abstractqueryexpansion', 'zbest_expanded_query']), ignore_index=True)
                    csv2json(df,'../ds/qs/{}/topics.clueweb12b13.{}.{}/'.format(db, ranker, metric))



