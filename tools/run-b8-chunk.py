#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run-b8-chunk.py — 轮式前台跑 b8（沙箱 504 收割后台进程的对策）
每轮从最大已有 part+1 跑 N 片或 TTL 自停。反复调用直至 40 片齐。
用法: python3 run-b8-chunk.py [N片=5] [TTL秒=540]
"""
import json, sys, time, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tool'))
from census_probe_py import probe
import concurrent.futures as cf

N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
TTL = int(sys.argv[2]) if len(sys.argv) > 2 else 540
os.chdir(os.path.dirname(os.path.abspath(__file__)))
bf = 'endpoints-batch8.txt'
pref = 'b8-shard-01'
urls = open(bf).read().split()
parts = sorted(int(p.rsplit('part', 1)[1].split('.')[0]) for p in glob.glob(f'shards/{pref}-part*.json'))
start = (parts[-1] + 1) if parts else 0
nparts = (len(urls) + 24) // 25
t0 = time.time()
from collections import Counter
done = 0
for part in range(start, nparts):
    if done >= N or time.time() - t0 > TTL:
        break
    chunk = urls[part * 25:(part + 1) * 25]
    if not chunk: break
    with cf.ThreadPoolExecutor(8) as ex:
        out = list(ex.map(probe, chunk))
    json.dump({"batch_file": bf, "shard": 1, "part": part, "results": out},
              open(f'shards/{pref}-part{part}.json', 'w'), ensure_ascii=False, indent=1)
    print('part', part, dict(Counter(r['v1'] for r in out)), flush=True)
    done += 1
print(f'CHUNK-DONE done={done} at_part={start+done-1} total_parts={nparts}', flush=True)
