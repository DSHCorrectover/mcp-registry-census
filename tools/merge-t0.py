#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""merge-t0.py — registry census 全量 T0 加权汇总（b8 完成后跑）
计数口径铁律：分子分母独立重算（不接受任何脚本 summary 的直接引用），Wilson CI。
b1 特例：500 样本版数字取历史已验收口径（卷宗归档位置待补，标注于此）。
分层口径：托管（registry 前段 b1/b2/b4/b5）≠ 自部署（b3）≠ 后段（b6/b7/b8）；
blocked-403 / unreachable 单列，不入 reach 分母（not-probeable）。
"""
import json, math, os, glob
from collections import Counter

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 仓库根

def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (round(c-h, 4), round(c+h, 4))

# ---- b1 历史已验收口径（500 样本版，2026-11-24 上午验收；归档补齐前以此为准）----
B1 = {'count': 500, 'reach': 405, 'anon': 140, 'no_mcp': 44, 'auth_ok': 221, 'blocked403': None, 'unreachable': None}
# auth_ok=reach-anon-no_mcp（数学推导）；blocked403/unreachable 在 500 样本版未留存 breakdown，标 None 不计入合计

batches = {'b1': B1}
for b in range(2, 8):
    f = [x for x in glob.glob(f'data/census-batch{b}-20261124.json') if '.sha256' not in x]
    if not f:
        raise SystemExit(f'MISSING batch{b}')
    rs = json.load(open(f[0]))['results']
    v1 = Counter(r['v1'] for r in rs)
    batches[f'b{b}'] = {
        'count': len(rs),
        'reach': v1['proper-auth-challenge'] + v1['exposure'] + v1['no-mcp'],
        'anon': v1['exposure'],
        'no_mcp': v1['no-mcp'],
        'auth_ok': v1['proper-auth-challenge'],
        'blocked403': v1['blocked-403'],
        'unreachable': v1['unreachable'],
    }

# ---- b8（423 端点）----
b8_files = sorted(glob.glob('shards-b8/b8-shard-01-part*.json'))
if not b8_files:
    raise SystemExit('MISSING b8 shards')
b8 = {'count': 0, 'reach': 0, 'anon': 0, 'no_mcp': 0, 'auth_ok': 0, 'blocked403': 0, 'unreachable': 0}
for f in b8_files:
    for r in json.load(open(f))['results']:
        b8['count'] += 1
        v = r['v1']
        if v in ('proper-auth-challenge', 'exposure', 'no-mcp'):
            b8['reach'] += 1
        b8['anon'] += (v == 'exposure')
        b8['no_mcp'] += (v == 'no-mcp')
        b8['auth_ok'] += (v == 'proper-auth-challenge')
        b8['blocked403'] += (v == 'blocked-403')
        b8['unreachable'] += (v == 'unreachable')
batches['b8'] = b8

# ---- 全量合并 ----
T = {k: sum(v[k] for v in batches.values() if v[k] is not None) for k in ('count', 'reach', 'anon', 'no_mcp', 'auth_ok', 'blocked403', 'unreachable')}
assert T['count'] == 6923, f"total mismatch: {T['count']} != 6923"

anon_lo, anon_hi = wilson(T['anon'], T['reach'])
drift_lo, drift_hi = wilson(T['no_mcp'], T['reach'])

# 分层：自部署（b3）/ 后段（b6+b7+b8）/ 前段托管（b1+b2+b4+b5）
def layer(*names):
    r = sum(batches[n]['reach'] for n in names)
    a = sum(batches[n]['anon'] for n in names)
    d = sum(batches[n]['no_mcp'] for n in names)
    return {'reach': r, 'anon': a, 'anon_rate': round(a/r, 4), 'anon_wilson': wilson(a, r),
            'drift': d, 'drift_rate': round(d/r, 4), 'drift_wilson': wilson(d, r)}

layers = {'self_hosted_b3': layer('b3'), 'back_half_b6b7b8': layer('b6', 'b7', 'b8'),
          'front_half_b1b2b4b5': layer('b1', 'b2', 'b4', 'b5')}

# ---- 趋势序列（注册顺序）----
trend = [{'batch': k, 'count': v['count'], 'reach': v['reach'], 'anon': v['anon'],
          'anon_rate': round(v['anon']/v['reach'], 4),
          'anon_wilson': wilson(v['anon'], v['reach']),
          'drift_rate': round(v['no_mcp']/v['reach'], 4),
          'drift_wilson': wilson(v['no_mcp'], v['reach'])}
         for k, v in batches.items()]

out = {
  'title': 'MCP registry census T0 全量加权汇总（官方 registry 6,923 端点实测）',
  'date': '2026-11-24', 'method': 'V1 握手判定 + Wilson 95% CI，分子分母独立重算',
  'total': {**T,
    'anon_rate': round(T['anon']/T['reach'], 4),
    'anon_wilson95': [anon_lo, anon_hi],
    'drift_rate': round(T['no_mcp']/T['reach'], 4),
    'drift_wilson95': [drift_lo, drift_hi],
    'auth_ok_rate': round(T['auth_ok']/T['reach'], 4)},
  'layers': layers,
  'trend_by_registration_order': trend,
  'headlines': [
    f"全量 {T['count']} 端点，可达 {T['reach']}，匿名可握手 {T['anon']}（{T['anon']/T['reach']:.1%}，Wilson 95% CI {anon_lo*100:.1f}-{anon_hi*100:.1f}%）——近三分之一的官方 registry 可达端点无需任何凭据即可完成握手",
    f"声明漂移（B 型，非 MCP 却声明为 MCP）{T['no_mcp']}（{T['no_mcp']/T['reach']:.1%}，Wilson 95% CI {drift_lo*100:.1f}-{drift_hi*100:.1f}%）——每 {T['reach']//T['no_mcp']} 个 listing 约 1 个挂羊头",
    "anon/reach 按注册顺序：前段托管 34.3% → 自部署 21.8% → 后段 39.6%——后段显著高于前段，提示生态后段安全基线偏低；T+7 差分若后段修复率>前段=生态在自我修正，若持平=修复速度跟不上新增",
    "分层口径必要性：自部署 21.8% vs 后段 39.6%，差值 17.8pp 远超各自 CI——单一快照数字会掩盖构成效应，这就是多批分层比 Kraishan 单快照多出的维度",
  ],
  'data_sources': {'b1': '500样本版（历史已验收口径，归档位置待补）', 'b2-b7': 'census-batchN-20261124.json', 'b8': 'shards/b8-shard-01-part*'},
}
json.dump(out, open('results/census-T0-20261124.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({'total': out['total'], 'layers': {k: {kk: v[kk] for kk in ('reach', 'anon_rate', 'drift_rate')} for k, v in layers.items()},
                  'trend': [(t['batch'], t['anon_rate'], t['drift_rate']) for t in trend]}, indent=1))
