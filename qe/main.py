#TODO: list all library requirements such as stemmers, tagme, ...
import os, traceback, operator, sys, math
from os import path
import pandas as pd
import argparse
import json
from pyserini.search import querybuilder
from pyserini.search import SimpleSearcher

#build anserini (maven) for doing A) indexing, B) information retrieval, and C) evaluation
#A) INDEX DOCUMENTS
#robust04
#$> query_expansion/anserini/target/appassembler/bin/IndexCollection -collection TrecCollection -input Robust04-Corpus -index lucene-index.robust04.pos+docvectors+rawdocs -generator JsoupGenerator -threads 44 -storePositions -storeDocvectors -storeRawDocs 2>&1 | tee log.robust04.pos+docvectors+rawdocs &
#Already done in https://git.uwaterloo.ca/jimmylin/anserini-indexes/raw/master/index-robust04-20191213.tar.gz

# Gov2:
#$> query_expansion/anserini/target/appassembler/bin/IndexCollection -collection TrecwebCollection -input Gov2-Corpus -index lucene-index.gov2.pos+docvectors+rawdocs -generator JsoupGenerator -threads 44 -storePositions -storeDocvectors -storeRawDocs 2>&1 | tee log.gov2.pos+docvectors+rawdocs &

# ClueWeb09-B-Corpus:
#$> query_expansion/anserini/target/appassembler/bin/IndexCollection -collection ClueWeb09Collection -input ClueWeb09-B-Corpus -index lucene-index.cw09b.pos+docvectors+rawdocs -generator JsoupGenerator -threads 44 -storePositions -storeDocvectors -storeRawDocs 2>&1 | tee  log.cw09b.pos+docvectors+rawdocs &

# ClueWeb12-B-Corpus:
#$> query_expansion/anserini/target/appassembler/bin/IndexCollection -collection ClueWeb12Collection -input ClueWeb12-B-Corpus -index lucene-index.cw12b13.pos+docvectors+rawdocs -generator JsoupGenerator -threads 44 -storePositions -storeDocvectors -storeRawDocs 2>&1 | tee  log.cw12b13.pos+docvectors+rawdocs &


#B) INFORMATION RETREIVAL: Ranking & Reranking
#$> query_expansion/anserini/target/appassembler/bin/SearchCollection -bm25 -threads 44 -topicreader Trec -index query_expansion/ds/robust04/index-robust04-20191213 -topics query_expansion/ds/robust04/topics.robust04.txt -output query_expansion/ds/robust04/topics.robust04.bm25.txt

#C) EVAL
#$> eval/trec_eval.9.0.4/trec_eval -q -m map query_expansion/ds/robust04/qrels.robust04.txt query_expansion/ds/robust04/topics.robust04.bm25.map.txt


#q: query
#Q: set of queries
#q_: expanded query (q')
#Q_: set of expanded queries(Q')

from cmn import expander_factory as ef
from cmn import utils
from expanders.abstractqexpander import AbstractQExpander
from expanders.onfields import OnFields

def generate(Qfilename, expanders, output):
    df = pd.DataFrame()
    model_errs = dict()
    for model in expanders:
        model_name = model.get_model_name()
        try:
            Q_filename = '{}.{}.txt'.format(output, model_name)
            # if not os.path.isfile(Q_filename) or overwrite:
            model.write_expanded_queries(Qfilename, Q_filename)
        except:
            model_errs[model_name] = traceback.format_exc()
            continue
    for model_err, msg in model_errs.items():
        print('INFO: MAIN: GENERATE: There has been error in {}!\n{}'.format(model_err, msg))

def search(expanders, rankers, topicreader, index, anserini, output):
    # Information Retrieval using Anserini
    rank_cmd = '{}target/appassembler/bin/SearchCollection'.format(anserini)
    model_errs = dict()

    for model in expanders:
        model_name = model.get_model_name()
        try:
            Q_filename = '{}.{}.txt'.format(output, model_name)
            for ranker in rankers:

                Q_pred = '{}.{}.{}.txt'.format(output, model_name, ef.get_ranker_name(ranker))
                q_dic={}
                searcher = SimpleSearcher(index)
                if ranker =='bm25':
                    searcher.set_bm25(0.9, 0.4)
                elif ranker =='qld':
                    searcher.set_qld()

                if isinstance(model, OnFields):
                    run_file=open(Q_pred,'w')
                    list_of_raw_queries=utils.get_raw_query(topicreader,Q_filename)
                    for qid,query in list_of_raw_queries.items():
                        q_text=utils.convert_onfield_query_format(query)
                        q_dic[qid.strip()]= json.loads(q_text)
                    for qid in q_dic.keys():
                        boost=[]
                        for q_terms,q_weights in q_dic[qid].items():
                            try:
                                boost.append( querybuilder.get_boost_query(querybuilder.get_term_query(q_terms),q_weights))
                            except:
                                # term do not exist in the indexed collection () e.g., stop words
                                pass

                        should = querybuilder.JBooleanClauseOccur['should'].value
                        boolean_query_builder = querybuilder.get_boolean_query_builder()
                        for boost_i in boost:
                            boolean_query_builder.add(boost_i, should)

                        query = boolean_query_builder.build()
                        hits = searcher.search(query,k=10000)
                        for i in range(0, 1000):
                            run_file.write(f'{qid} Q0  {hits[i].docid:15} {i+1:2}  {hits[i].score:.5f} Pyserini \n')
                    run_file.close()


                else:
                    cli_cmd = '\"{}\" {} -threads 44 -topicreader {} -index {} -topics {} -output {}'.format(rank_cmd, ranker, topicreader, index, Q_filename, Q_pred)
                    print('{}\n'.format(cli_cmd))
                    stream = os.popen(cli_cmd)
                    print(stream.read())
        except:
            model_errs[model_name] = traceback.format_exc()
            continue
    for model_err, msg in model_errs.items():
        print('INFO: MAIN: SEARCH: There has been error in {}!\n{}'.format(model_err, msg))

def evaluate(expanders, Qrels, rankers, metrics, anserini, output):
    # Evaluation using trec_eval
    eval_cmd = '{}eval/trec_eval.9.0.4/trec_eval'.format(anserini)
    model_errs = dict()

    for model in expanders:
        model_name = model.get_model_name()
        try:
            for ranker in rankers:
                Q_pred = '{}.{}.{}.txt'.format(output, model_name, ef.get_ranker_name(ranker))
                for metric in metrics:
                    Q_eval = '{}.{}.{}.{}.txt'.format(output, model_name, ef.get_ranker_name(ranker), metric)
                    cli_cmd = '\"{}\" -q -m {} {} {} > {}'.format(eval_cmd, metric, Qrels, Q_pred, Q_eval)
                    print('{}\n'.format(cli_cmd))
                    stream = os.popen(cli_cmd)
                    print(stream.read())
        except:
            model_errs[model_name] = traceback.format_exc()
            continue
    for model_err, msg in model_errs.items():
        print('INFO: MAIN: EVALUATE: There has been error in {}!\n{}'.format(model_err, msg))

def aggregate(expanders, rankers, metrics, output):
    df = pd.DataFrame()
    model_errs = dict()
    queryids = pd.DataFrame()
    for model in expanders:
        model_name = model.get_model_name()
        # try:
        Q_filename = '{}.{}.txt'.format(output, model_name)
        Q_ = model.read_expanded_queries(Q_filename)
        for ranker in rankers:
            for metric in metrics:
                Q_eval = '{}.{}.{}.{}.txt'.format(output, model_name, ef.get_ranker_name(ranker), metric)
                #the last row is average over all. skipped by [:-1]
                values = pd.read_csv(Q_eval, usecols=[1,2],names=['qid', 'value'], header=None,sep='\t')[:-1]
                values.set_index('qid', inplace=True, verify_integrity=True)

                for idx, r in Q_.iterrows():
                    Q_.loc[idx, '{}.{}.{}'.format(model_name, ef.get_ranker_name(ranker), metric)] = values.loc[str(r.qid), 'value'] if str(r.qid) in values.index else None

        # except:
        #     model_errs[model_name] = traceback.format_exc()
        #     continue
        df = pd.concat([df, Q_], axis=1)

    filename = '{}.{}.{}.all.csv'.format(output, '.'.join([ef.get_ranker_name(r) for r in rankers]), '.'.join(metrics))
    df.to_csv(filename, index=False)
    # for model_err, msg in model_errs.items():
    #     print('INFO: MAIN: AGGREGATE: There has been error in {}!\n{}'.format(model_err, msg))
    return filename

def build(input, expanders, rankers, metrics, output):
    base_model_name = AbstractQExpander().get_model_name()
    df = pd.read_csv(input)
    ds_df = df.iloc[:, :1+1+len(rankers)*len(metrics)]#the original query info
    ds_df['star_model_count'] = 0
    for idx, row in df.iterrows():
        star_models = dict()
        for model in expanders:
            model_name = model.get_model_name()
            if model_name == base_model_name:
                continue
            flag = True
            sum = 0
            for ranker in rankers:
                for metric in metrics:
                    v = df.loc[idx, '{}.{}.{}'.format(model_name, ef.get_ranker_name(ranker), metric)]
                    v = v if not pd.isna(v) else 0
                    v0 = df.loc[idx, '{}.{}.{}'.format(base_model_name, ef.get_ranker_name(ranker), metric)]
                    v0 = v0 if not pd.isna(v0) else 0
                    if v <= v0:
                        flag = False
                        break
                    sum += v ** 2
            if flag:
                star_models[model] = sum

        if len(star_models) > 0:
            ds_df.loc[idx, 'star_model_count'] = len(star_models.keys())
            star_models_sorted = {k: v for k, v in sorted(star_models.items(), key=lambda item: item[1], reverse=True)}
            for i, star_model in enumerate(star_models_sorted.keys()):
                ds_df.loc[idx, '{}.{}'.format('method', i + 1)] = star_model.get_model_name()
                ds_df.loc[idx, '{}.{}'.format('metric', i + 1)] = math.sqrt(star_models[star_model])
                ds_df.loc[idx, '{}.{}'.format('query', i + 1)] = df.loc[idx, '{}'.format(star_model.get_model_name())]
        else:
            ds_df.loc[idx, 'star_model_count'] = 0
    filename = '{}.{}.{}.dataset.csv'.format(output, '.'.join([ef.get_ranker_name(r) for r in rankers]), '.'.join(metrics))
    ds_df.to_csv(filename, index=False)
    return filename

def run(db, rankers, metrics, output, ext_corpus, ext_prels, rf=True, op=[]):

    if db == 'robust04':
        #/data/anserini/lucene-index.robust04.pos+docvectors+rawdocs
        output_ = '{}topics.robust04'.format(output)
        expanders = ef.get_nrf_expanders()
        if rf:#local analysis
            expanders += ef.get_rf_expanders(rankers=rankers, corpus=db, output=output_, ext_corpus=ext_corpus,ext_prels=ext_prels)

        if 'generate' in op:generate(Qfilename='../ds/robust04/topics.robust04.txt', expanders=expanders, output=output_)
        if 'search' in op:search(  expanders=expanders, rankers=rankers, topicreader='Trec', index=param.database[db]['index'], anserini=param.anserini['path'], output=output_)
        if 'evaluate' in op:evaluate(expanders=expanders, Qrels='../ds/robust04/qrels.robust04.txt', rankers=rankers, metrics=metrics, anserini=anserini, output=output_)
        if 'build' in op:
            result = aggregate(expanders=expanders, rankers=rankers,metrics=metrics, output=output_)
            build(input=result, expanders=expanders, rankers=rankers,metrics=metrics, output=output_)

    if db == 'gov2':
        # index = '/data/anserini/lucene-index.gov2.pos+docvectors+rawdocs'
        topicreader = 'Trec'

        results = []
        for r in ['4.701-750', '5.751-800', '6.801-850']:
            output_ = '{}topics.terabyte0{}'.format(output, r)

            expanders = ef.get_nrf_expanders()
            if rf:
                expanders += ef.get_rf_expanders(rankers=rankers, corpus=db, output=output_, ext_corpus=ext_corpus,ext_prels=ext_prels)

            if 'generate' in op:generate(Qfilename='../ds/gov2/{}.terabyte0{}.txt'.format('topics', r), expanders=expanders, output=output_)
            if 'search' in op:search(  expanders=expanders, rankers=rankers, topicreader=topicreader, index=param.database[db]['index'], anserini=param.anserini['path'], output=output_)
            if 'evaluate' in op:evaluate(expanders=expanders, Qrels='../ds/gov2/qrels.terabyte0{}.txt'.format(r), rankers=rankers, metrics=metrics, anserini=anserini, output=output_)
            if 'build' in op:
                result = aggregate(expanders=expanders, rankers=rankers, metrics=metrics, output=output_)
                result = build(input=result, expanders=expanders, rankers=rankers, metrics=metrics, output=output_)
                results.append(result)

        if 'build' in op:
            output_ = results[0].replace(results[0].split('/')[-1].split('.')[1], 'gov2').replace(results[0].split('/')[-1].split('.')[2], '701-850')
            df = pd.DataFrame()
            for r in results:
                df = pd.concat([df, pd.read_csv(r)], axis=0, ignore_index=True, sort=False)
            df.to_csv(output_, index=False)

    if db == 'clueweb09b':
        # index = '/data/anserini/lucene-index.cw09b.pos+docvectors+rawdocs'
        topicreader = 'Webxml'

        results = []
        for r in ['1-50', '51-100', '101-150', '151-200']:
            output_ = '{}topics.web.{}'.format(output, r)

            expanders = ef.get_nrf_expanders()
            if rf:
                expanders += ef.get_rf_expanders(rankers=rankers, corpus=db, output=output_, ext_corpus=ext_corpus,ext_prels=ext_prels)

            if 'generate' in op:generate(Qfilename='../ds/clueweb09b/topics.web.{}.txt'.format(r), expanders=expanders, output=output_)
            if 'search' in op:search(  expanders=expanders, rankers=rankers, topicreader=topicreader, index=param.database[db]['index'], anserini=param.anserini['path'], output=output_)
            if 'evaluate' in op:evaluate(expanders=expanders, Qrels='../ds/clueweb09b/qrels.web.{}.txt'.format(r), rankers=rankers, metrics=metrics, anserini=anserini, output=output_)
            if 'build' in op:
                result = aggregate(expanders=expanders, rankers=rankers, metrics=metrics, output=output_)
                result = build(input=result, expanders=expanders, rankers=rankers, metrics=metrics, output=output_)
                results.append(result)

        if 'build' in op:
            output_ = results[0].replace('.'+results[0].split('/')[-1].split('.')[1]+'.', '.clueweb09b.').replace(results[0].split('/')[-1].split('.')[2], '1-200')
            df = pd.DataFrame()
            for r in results:
                df = pd.concat([df, pd.read_csv(r)], axis=0, ignore_index=True, sort=False)
            df.to_csv(output_, index=False)

    if db == 'clueweb12b13':
        # index = '/data/anserini/lucene-index.cw12b13.pos+docvectors+rawdocs'
        topicreader = 'Webxml'
        results = []
        for r in ['201-250', '251-300']:
            output_ = '{}topics.web.{}'.format(output, r)

            expanders = ef.get_nrf_expanders()
            if rf:
                expanders += ef.get_rf_expanders(rankers=rankers, corpus=db, output=output_, ext_corpus=ext_corpus,ext_prels=ext_prels)

            if 'generate' in op:generate(Qfilename='../ds/clueweb12b13/topics.web.{}.txt'.format(r), expanders=expanders, output=output_)
            if 'search' in op:search(expanders=expanders, rankers=rankers, topicreader=topicreader, index=param.database[db]['index'], anserini=param.anserini['path'], output=output_)
            if 'evaluate' in op:evaluate(expanders=expanders, Qrels='../ds/clueweb12b13/qrels.web.{}.txt'.format(r), rankers=rankers, metrics=metrics, anserini=anserini, output=output_)
            if 'build' in op:
                result = aggregate(expanders=expanders, rankers=rankers, metrics=metrics, output=output_)
                result = build(input=result, expanders=expanders, rankers=rankers, metrics=metrics, output=output_)
                results.append(result)

        if 'build' in op:
            output_ = results[0].replace('.'+results[0].split('/')[-1].split('.')[1]+'.', '.clueweb12b13.').replace(results[0].split('/')[-1].split('.')[2], '201-300')
            df = pd.DataFrame()
            for r in results:
                df = pd.concat([df, pd.read_csv(r)], axis=0, ignore_index=True, sort=False)
            df.to_csv(output_, index=False)

def addargs(parser):
    # anserini = parser.add_argument_group('Anserini')
    # anserini.add_argument('--anserini', type=str, default='../anserini/', help='The path to the anserini library (default: ../anserini/)')

    corpus = parser.add_argument_group('Corpus')
    corpus.add_argument('--corpus', type=str, choices=['robust04', 'gov2', 'clueweb09b', 'clueweb12b13'], required=True, help='The corpus name; required; (example: robust04)')
    # corpus.add_argument('--index', type=str, required=True, help='The corpus index; required; (example: ../ds/robust04/lucene-index.robust04.pos+docvectors+rawdocs)')

    gold = parser.add_argument_group('Gold Standard Dataset')
    gold.add_argument('--output', type=str, required=True, help='The output path for the gold standard dataset; required; (example: ../ds/qe/robust04/')
    gold.add_argument('--ranker', type=str, choices=['bm25', 'qld'], default='bm25', help='The ranker name (default: bm25)')
    gold.add_argument('--metric', type=str, choices=['map'], default='map', help='The evaluation metric name (default: map)')

    external_corpus = parser.add_argument_group('External Corpus')
    external_corpus.add_argument('--ext_corpus', type=str, choices=['robust04', 'gov2', 'clueweb09b', 'clueweb12b13'], help='The external corpus name; required only for AdapOnFields and OnFields; (example: robust04)')
    # external_corpus.add_argument('--ext_index', type=str, help='The external corpus index; required only for AdapOnFields and OnFields; (example: ../ds/robust04/lucene-index.robust04.pos+docvectors+rawdocs)')
    external_corpus.add_argument('--ext_prels',  type=str, help='Retrieval run results for external corpus; required only for AdapOnFields and OnFields; (example: ../ds/robust04/topics.robust04.txt)')
    # external_corpus.add_argument('--ext_collection_tokens' , type=int , help = 'Total Number of tokens in the external corpus; required only for AdapOnFields and OnFields; (example: 148000000 )')
    # external_corpus.add_argument('--ext_w_a' , type=float, help ='Weight for anchor fields in external corpus.required only for AdapOnFields and OnFields; (example: 1.0)')
    # external_corpus.add_argument('--ext_w_t', type = float, help ='Weight for title fields in external corpus.required only for AdapOnFields and OnFields; (example: 2.25)')
    # external_corpus.add_argument('--ext_corpus_size', type = int, help ='Total Number of documents in the external corpus; required only for AdapOnFields and OnFields; (example: 520000 )')


# # python -u main.py --corpus robust04 --output ../ds/qe/robust04/ --ranker bm25 --metric map 2>&1 | tee robust04.bm25.log &
# # python -u main.py --corpus robust04 --output ../ds/qe/robust04/ --ranker qld --metric map 2>&1 | tee robust04.qld.log &

# Example for OnFields and AdopOnFields:
# # python -u main.py --corpus robust04 --output ../ds/qe/robust04/ --ranker bm25 --metric map --ext_corpus gov2 --ext_prels ../ds/qe/gov2/topics.terabyte04.701-750.abstractqueryexpansion.bm25.txt 2>&1 | tee robust04.bm25.log &

# # python -u main.py --corpus gov2 --output ../ds/qe/gov2/ --ranker bm25 --metric map 2>&1 | tee gov2.bm25.log &
# # python -u main.py --corpus gov2 --output ../ds/qe/gov2/ --ranker qld --metric map 2>&1 | tee gov2.qld.log &

# # python -u main.py --corpus clueweb09b --output ../ds/qe/clueweb09b/ --ranker bm25 --metric map 2>&1 | tee clueweb09b.bm25.log &
# # python -u main.py --corpus clueweb09b --output ../ds/qe/clueweb09b/ --ranker qld --metric map 2>&1 | tee clueweb09b.qld.log &

# # python -u main.py --corpus clueweb12b13 --output ../ds/qe/clueweb12b13/ --ranker bm25 --metric map 2>&1 | tee clueweb12b13.bm25.log &
# # python -u main.py --corpus clueweb12b13 --output ../ds/qe/clueweb12b13/ --ranker qld --metric map 2>&1 | tee clueweb12b13.qld.log &


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ReQue (Refining Queries)')
    addargs(parser)
    args = parser.parse_args()

    ## rf: whether to include relevance feedback expanders (local analysis) or not
    ## op: determines the steps in the pipeline. op=['generate', 'search', 'evaluate', 'build']

    run(db=args.corpus.lower(),
        rankers=['-' + args.ranker.lower()],
        metrics=[args.metric.lower()],
        output=args.output,
        ext_corpus=args.ext_corpus,
        ext_prels=args.ext_prels,
        rf=True,
        op=['generate', 'search', 'evaluate', 'build'])
