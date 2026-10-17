"""Zero-solver frozen public ranking audit; see research-20261017/offline-ranking/PROTOCOL.md."""
from __future__ import annotations
import argparse, hashlib, json, math, os, random, time, traceback
from pathlib import Path
from collections import defaultdict
from egglab import claude_cases
from egglab import native_recharge as nr

WHITELIST = {'public:hildenbrand15': 'h15-learned4-T180-k30', 'public:eberbach': 'eb-learned4-T600-m5'}
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def heuristic(case):
    trips = {t.id:t for t in case.trips}
    values = []
    for m in case.movements:
        moving = sum(l.arrive_min-l.depart_min for l in m.legs if l.origin != l.destination)
        slack = trips[m.after].start_min-trips[m.before].end_min if m.before and m.after else 0
        dwell = m.legs[m.depot_split].depart_min-m.legs[m.depot_split-1].arrive_min if m.kind == 'depot' else 0
        values.append(-moving-.1*slack+.1*dwell)
    return values

def measure(case, reference, scores):
    flexible = [i for i,m in enumerate(case.movements) if m.kind in ('direct','depot')]
    boundaries = {i for i,m in enumerate(case.movements) if m.kind not in ('direct','depot')}
    ref = {i for i,m in enumerate(case.movements) if m.id in reference}
    if len(ref) != len(reference): raise ValueError('unknown reference movement')
    order = sorted(flexible, key=lambda i:(-scores[i], i))
    sides = {side:defaultdict(list) for side in ('incoming','outgoing')}
    for i in order:
        m=case.movements[i]; sides['incoming'][m.after].append(i); sides['outgoing'][m.before].append(i)
    metrics=[]
    def record(rule, kept, side_recall=None):
        metrics.append(dict(rule=rule, kept_flexible=len(kept-boundaries), total_flexible=len(flexible),
          reference_flexible=len(ref-boundaries), reference_flexible_kept=len((ref-boundaries)&kept),
          flexible_recall=len((ref-boundaries)&kept)/len(ref-boundaries) if ref-boundaries else 1.,
          complete_plan=ref<=kept, side_recall=side_recall))
    for n in range(1,9):
        kept=set(boundaries); recalls={}
        for side,buckets in sides.items():
            hit=den=0
            for trip in case.trips:
                candidates=buckets.get(trip.id,[]); selected=set(candidates[:n]); kept.update(selected)
                # Full-plan boundary edges are always retained; report flexible and all-trip denominators.
                relevant=ref & set(candidates)
                hit+=len(relevant & selected); den+=len(relevant)
            recalls[side]=dict(hits=hit, denominator=den, recall=hit/den if den else 1.)
        record(f'top{n}',kept,recalls)
    for fraction in (.05,.15,.30):
        base=set(order[:max(1,math.ceil(fraction*len(order)))] )|boundaries
        record(f'keep{int(fraction*100)}_pure',base)
        floor=set(base)
        for buckets in sides.values():
            for candidates in buckets.values(): floor.update(candidates[:3])
        record(f'keep{int(fraction*100)}_floor3',floor)
    return metrics

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--assets',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    started=time.monotonic(); out={'protocol':'PROTOCOL.md','failures':[], 'cases':[], 'hashes':{},'unavailable':['CatBoost v5 artifact','scale saved reference plans','cold-found reference plans','historical best public plans'], 'limits':'Two reused networks; learned-generated references favor v8; no optimum/test/generalization claim.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try:
        scorefile=args.assets/'e5-public-20261001/scores_v8_day.json'; out['hashes'][str(scorefile)]=sha(scorefile); saved=json.loads(scorefile.read_text())
        for key,folder in WHITELIST.items():
            t=time.monotonic(); path=args.assets/'runs/local-validate'/folder/'e3.json'; out['hashes'][str(path)]=sha(path)
            row=json.loads(path.read_text()); case=claude_cases.make(key)
            if row['case']!=key or row['case_identity']!=case.identity(): raise ValueError('reference identity mismatch')
            nr.replay_native(case,row['plan'])
            reference={m for v in row['plan']['vehicles'] for m in v['movements']}
            score=saved[key]
            if score['case_identity']!=case.identity() or score['movement_ids']!=[m.id for m in case.movements]: raise ValueError('score identity mismatch')
            ranks={'v8':score['logits'],'heuristic':heuristic(case)}
            for seed in range(20):
                rng=random.Random(seed); ranks[f'random{seed:02}']=[rng.random() for _ in case.movements]
            out['cases'].append(dict(case=key,network=key.split(':')[1].rstrip('0123456789'),reference_source=str(path),reference_bill=row['bill'],reference_kind='best available feasible (one candidate)',score_seconds_archived=score['score_seconds'],rankings={name:measure(case,reference,values) for name,values in ranks.items()},seconds=time.monotonic()-t))
        grouped=defaultdict(list)
        for case in out['cases']:
            for rank,metrics in case['rankings'].items():
                arm='random' if rank.startswith('random') else rank
                for metric in metrics: grouped[(case['network'],arm,metric['rule'])].append(metric)
        out['network_aggregates']=[dict(network=n,arm=a,rule=r,replicates=len(rows),flexible_recall=sum(x['flexible_recall'] for x in rows)/len(rows),complete_plan_rate=sum(x['complete_plan'] for x in rows)/len(rows)) for (n,a,r),rows in grouped.items()]
        across=defaultdict(list)
        for row in out['network_aggregates']: across[(row['arm'],row['rule'])].append(row)
        out['equal_network_aggregates']=[dict(arm=a,rule=r,networks=len(rows),flexible_recall=sum(x['flexible_recall'] for x in rows)/len(rows),complete_plan_rate=sum(x['complete_plan_rate'] for x in rows)/len(rows)) for (a,r),rows in across.items()]
        for payload in Path('data/public/sistig_26088190_v1').glob('*native_case*.json'): out['hashes'][str(payload)]=sha(payload)
    except Exception:
        out['failures'].append(traceback.format_exc())
    finally:
        for source in (Path(__file__),Path('research-20261017/offline-ranking/PROTOCOL.md'),Path('src/egglab/claude_cases.py'),Path('src/egglab/native_recharge.py')):
            out['hashes'][str(source)]=sha(source)
        out['seconds']=time.monotonic()-started; out['threads']={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')}; args.output.write_text(json.dumps(out,indent=2)+'\n')
    if out['failures']: raise SystemExit(1)
if __name__=='__main__': main()
