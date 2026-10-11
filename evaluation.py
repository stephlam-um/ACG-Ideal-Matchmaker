"""Reproducible random@5 and exact-tag retrieval proxy, plus dense latency."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
import numpy as np
from pipeline import CHAR_DATA_PATH, EMBEDDINGS_PATH, load_character_data, load_embeddings, match_user
from retrieval import CosineIndex, TraitIndex


def recall_at_k(ranking, relevant, k=5):
    relevant=set(relevant)
    if not relevant:
        raise ValueError('Recall requires at least one relevant item.')
    return len(set(ranking[:k]) & relevant)/len(relevant)


def random_ranking(size,k,rng):
    return rng.choice(size,size=min(k,size),replace=False).tolist()


def bootstrap_interval(values, rng):
    values=np.asarray(values)
    samples=rng.choice(values,size=(2000,len(values)),replace=True).mean(axis=1)
    return np.quantile(samples,[.025,.975]).tolist()


def evaluate(seed=42, repeats=4):
    characters=load_character_data(CHAR_DATA_PATH)
    vectors=load_embeddings(EMBEDDINGS_PATH)
    rng=np.random.default_rng(seed)
    index=TraitIndex(characters)
    cases=[]
    # All characters are represented equally. Names and IDs never enter queries.
    for target,character in enumerate(characters):
        traits=sorted(set(character['moe_traits']))
        for repeat in range(repeats):
            query=rng.choice(traits,size=min(3,len(traits)),replace=False).tolist()
            cases.append({'case_id':f'{target}-{repeat}','traits':query,'relevant_ids':[target]})
    rng.shuffle(cases)
    random_values=[]; tag_values=[]; details=[]
    random_trials=np.zeros(1000)
    for case in cases:
        baseline=random_ranking(len(characters),5,rng)
        ranked=[i for i,_ in index.search(case['traits'],5)]
        rv=recall_at_k(baseline,case['relevant_ids']); tv=recall_at_k(ranked,case['relevant_ids'])
        random_values.append(rv); tag_values.append(tv)
        for trial in range(len(random_trials)):
            random_trials[trial]+=recall_at_k(random_ranking(len(characters),5,rng),case['relevant_ids'])/len(cases)
        details.append({**case,'random_top5':baseline,'trait_top5':ranked,'random_recall':rv,'trait_recall':tv})
    # Multiple cases from one character are correlated: bootstrap character means.
    grouped=[np.mean([d['trait_recall'] for d in details if d['relevant_ids']==[i]]) for i in range(len(characters))]
    start=perf_counter(); dense=CosineIndex(vectors); build_ms=(perf_counter()-start)*1000
    queries=np.random.default_rng(seed+1).normal(size=(2000,vectors.shape[1]))
    timings={'reference':[],'prepared':[]}; identical=True
    for query in queries[:20]:
        match_user(query,vectors); dense.search(query)
    for query in queries:
        # Alternate order to reduce systematic timing bias.
        methods=[('reference',lambda:match_user(query,vectors)),('prepared',lambda:dense.search(query))]
        if len(timings['reference'])%2: methods.reverse()
        results={}
        for name,method in methods:
            start=perf_counter(); results[name]=method(); timings[name].append((perf_counter()-start)*1000)
        identical &= [i for i,_ in results['reference']] == [i for i,_ in results['prepared']]
        np.testing.assert_allclose([s for _,s in results['reference']],[s for _,s in results['prepared']],atol=1e-8)
    sensitivity=[]
    for trait_count in (1,2,3):
        trial_rng=np.random.default_rng(seed+trait_count)
        hits1=[];hits5=[]
        for target,character in enumerate(characters):
            tags=sorted(set(character['moe_traits']))
            for _ in range(repeats):
                query=trial_rng.choice(tags,size=min(trait_count,len(tags)),replace=False).tolist()
                ranking=[i for i,_ in index.search(query,5)]
                hits1.append(recall_at_k(ranking,[target],1))
                hits5.append(recall_at_k(ranking,[target],5))
        sensitivity.append({'traits':trait_count,'queries':len(hits5),'recall_at_1':float(np.mean(hits1)),'recall_at_5':float(np.mean(hits5))})
    latency={name:{'median_ms':float(np.median(values)),'p95_ms':float(np.quantile(values,.95))} for name,values in timings.items()}
    summary={
        'tag_query_sensitivity':sensitivity,
        'seed':seed,'characters':len(characters),'queries':len(cases),'query_traits':3,'k':5,
        'protocol':'Synthetic partial-tag source-character retrieval. Single relevant source ID; other characters may also be relevant. Exact catalog tags are reused: optimistic proxy, not human relevance.',
        'catalog_sha256':hashlib.sha256(CHAR_DATA_PATH.read_bytes()).hexdigest(),
        'random_recall_at_5':float(np.mean(random_values)),
        'random_expected_recall_at_5':min(5,len(characters))/len(characters),
        'random_1000_trials_mean':float(random_trials.mean()),
        'random_1000_trials_95pct_range':np.quantile(random_trials,[.025,.975]).tolist(),
        'trait_recall_at_5':float(np.mean(tag_values)),
        'trait_character_bootstrap_95pct_ci':bootstrap_interval(grouped,np.random.default_rng(seed+2)),
        'dense_quality':'NOT EVALUATED: no query embeddings available; stored character vectors are not used as quality queries.',
        'latency_protocol':'2000 seeded random 1024D queries, same real corpus, 20 warmups, interleaved calls. Excludes LLM, embedding, index construction.',
        'index_build_ms':build_ms,'latency':latency,'top5_identical':bool(identical),
        'median_speedup':latency['reference']['median_ms']/latency['prepared']['median_ms'],
    }
    return summary,details


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--output',type=Path,default=Path('evaluation-results'))
    args=parser.parse_args()
    summary,details=evaluate(args.seed)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.output/'cases.json').write_text(json.dumps(details,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
