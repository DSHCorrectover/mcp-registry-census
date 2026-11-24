# 断点续传 runner：从最大已有 part+1 起，跑到 TTL 上限
# 用法: python3 tool/b4runner.py [TTL秒] [batch文件] [前缀]
import json, sys, time, os, glob
sys.path.insert(0, os.path.dirname(__file__))
from census_probe_py import probe
import concurrent.futures as cf

TTL=int(sys.argv[1]) if len(sys.argv)>1 else 100
bf=sys.argv[2] if len(sys.argv)>2 else 'endpoints-batch4.txt'
pref=sys.argv[3] if len(sys.argv)>3 else 'b4-shard-01'
urls=open(bf).read().split()
parts=sorted(int(p.rsplit('part',1)[1].split('.')[0]) for p in glob.glob(f'shards/{pref}-part*.json'))
start=(parts[-1]+1) if parts else 0
t0=time.time(); nparts=(len(urls)+24)//25
from collections import Counter
for part in range(start, nparts):
    if time.time()-t0>TTL:
        print('TTL stop at part', part); break
    chunk=urls[part*25:(part+1)*25]
    if not chunk: break
    with cf.ThreadPoolExecutor(8) as ex:
        out=list(ex.map(probe, chunk))
    json.dump({"batch_file":bf,"shard":1,"part":part,"results":out},
              open(f'shards/{pref}-part{part}.json','w'), ensure_ascii=False, indent=1)
    print('part', part, dict(Counter(r['v1'] for r in out)), flush=True)
