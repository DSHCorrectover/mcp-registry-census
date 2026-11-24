#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""trend-charts.py — 六/八批趋势图（注册顺序 vs 暴露率 + 声明漂移），带 Wilson CI 误差棒"""
import json, os
import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager
import matplotlib.pyplot as plt
font_manager.fontManager.addfont('/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-ExtraBold.ttf')
font_manager.fontManager.addfont('/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Black.ttf')
plt.rcParams['font.family']=['Noto Serif SC']
plt.rcParams['axes.unicode_minus']=False

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 仓库根
t = json.load(open('results/census-T0-20261124.json'))
tr = t['trend_by_registration_order']
x = list(range(len(tr)))
labels = [d['batch'] for d in tr]

def draw(vals, lo_hi, title, ylabel, fname, color, ref=None, ref_label=None):
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
    y = [v*100 for v in vals]
    err = [[(y[i]-lo_hi[i][0]*100) for i in x], [(lo_hi[i][1]*100-y[i]) for i in x]]
    ax.errorbar(x, y, yerr=err, fmt='o-', color=color, capsize=4, linewidth=1.8, markersize=6)
    for i, v in enumerate(y):
        ax.annotate(f"{v:.1f}%", (x[i], v), textcoords="offset points", xytext=(0, 9),
                    ha='center', fontsize=8.5, color='#333')
    if ref is not None:
        ax.axhline(ref*100, ls='--', lw=1, color='#999')
        ax.annotate(ref_label, (len(x)-1, ref*100), textcoords="offset points",
                    xytext=(-4, 6), ha='right', fontsize=8, color='#666')
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_xlabel('Registry 扫描批次（注册顺序）', fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=11.5, fontweight='bold')
    ax.grid(axis='y', alpha=.3); ax.set_ylim(0, max(y)*1.35)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(fname, bbox_inches='tight'); plt.close(fig)
    print('saved', fname)

draw([d['anon_rate'] for d in tr], [d['anon_wilson'] for d in tr],
     '匿名握手率 by 批次（官方 registry 可达端点，Wilson 95% CI）',
     '匿名可握手 / 可达端点', 'trend-anon-20261124.png', '#c0392b',
     ref=t['total']['anon_rate'], ref_label=f"全量加权 {t['total']['anon_rate']*100:.1f}%")

draw([d['drift_rate'] for d in tr], [d['drift_wilson'] for d in tr],
     '声明漂移率（B 型：非 MCP 却声明为 MCP）by 批次',
     '漂移 / 可达端点', 'trend-drift-20261124.png', '#2471a3',
     ref=t['total']['drift_rate'], ref_label=f"全量加权 {t['total']['drift_rate']*100:.1f}%")
