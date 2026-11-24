#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify.py — CI 数据锁+复现自检（9+9 复检入口之一）
1. MANIFEST.sha256 逐文件校验（数据锁）
2. T0 汇总独立重算对账：分批和=6923、anon/drift 率、Wilson CI 双实现一致、后段分层
exit≠0 = 任何一项 FAIL，禁止发布。
"""
import json, hashlib, math, sys, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 仓库根（tools/ 的父目录）
fail = []

def check(name, ok, detail=''):
    print(('PASS' if ok else 'FAIL'), name, detail)
    if not ok: fail.append(name)

# 1. 数据锁
man = {}
try:
    for line in open('MANIFEST.sha256'):
        h, f = line.split(maxsplit=1)
        man[f.strip()] = h
    bad = []
    for f, h in man.items():
        d = hashlib.sha256(open(f, 'rb').read()).hexdigest()
        if d != h: bad.append(f)
    check('manifest_sha256', not bad and len(man) >= 15, f'{len(man)} files, bad={bad}')
except FileNotFoundError:
    check('manifest_sha256', False, 'MANIFEST.sha256 missing')

# 2. T0 重算对账
def wilson(k, n, z=1.96):
    p = k/n; d = 1+z*z/n; c = (p+z*z/(2*n))/d; h = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (round(c-h, 4), round(c+h, 4))

try:
    t = json.load(open('results/census-T0-20261124.json'))['total']
    check('total_count_6923', t['count'] == 6923, t['count'])
    check('total_reach_3602', t['reach'] == 3602, t['reach'])
    check('anon_rate', abs(t['anon_rate'] - t['anon']/t['reach']) < 5.1e-5)
    check('drift_rate', abs(t['drift_rate'] - t['no_mcp']/t['reach']) < 5.1e-5)
    check('anon_wilson', list(wilson(t['anon'], t['reach'])) == t['anon_wilson95'])
    check('drift_wilson', list(wilson(t['no_mcp'], t['reach'])) == t['drift_wilson95'])
    d = json.load(open('results/census-T0-20261124.json'))
    tr = d['trend_by_registration_order']
    check('batch_sum_6923', sum(x['count'] for x in tr) == 6923)
    bh = [x for x in tr if x['batch'] in ('b6', 'b7', 'b8')]
    r = sum(x['reach'] for x in bh); a = sum(x['anon'] for x in bh)
    check('backhalf_layer', abs(a/r - d['layers']['back_half_b6b7b8']['anon_rate']) < 5.1e-5, f'{a/r:.4f}')
except Exception as e:
    check('t0_recompute', False, str(e)[:120])

print('=' * 40)
if fail:
    print(f'VERIFY FAIL ({len(fail)}): {fail}'); sys.exit(1)
print('VERIFY ALL PASS')
