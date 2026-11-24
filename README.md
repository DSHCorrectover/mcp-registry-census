# mcp-registry-census — MCP 官方 Registry 全量安全普查 T0 快照（确权 v1.0）

**Correctover = AI Reliability** | 确权主体：王桂桂（Guigui Wang）| T0: 2026-11-24

官方 MCP registry（registry.modelcontextprotocol.io）声明 20,000 server 中实际探得 **6,923 可达端点**，八批次全量普查：

| 指标 | 值 | Wilson 95% CI |
|---|---|---|
| 匿名可握手/可达 | **36.5%**（1,313/3,602） | [34.9%, 38.0%] |
| 声明漂移（非MCP却声明MCP）/可达 | **12.9%**（465/3,602） | [11.9%, 14.0%] |
| 认证健全/可达 | 50.6% | — |
| blocked-403 / unreachable | 1,289 / 1,936 | 单列不入分母 |

**分层**：前段托管 35.0% ｜ 自部署 21.8% ｜ 后段 **44.6%**（最新批 b8 单批 **60.2%**——新增供给安全基线更低）
**T+7 差分**：2026-12-01 复测（本仓为 T0 基线；后段修复>前段=生态自修正，持平=修复跟不上新增）

## 引用

**DOI: [10.5281/zenodo.24496532](https://doi.org/10.5281/zenodo.24496532)**（Zenodo, CC0）· Wang, Guigui (2026). *MCP Registry Security Census T0 (2026-11-24): 6,923 endpoints, full-coverage exposure survey.*

## 可复现（Reproduce）

```bash
# 1. 环境自检（CI 同款）：数据锁 + 汇总重算对账
python3 tools/verify.py

# 2. 全量 T0 汇总重算（独立重算分子分母，不信任何中间 summary）
python3 tools/merge-t0.py

# 3. 趋势图重绘
python3 tools/trend-charts.py
```

探针实现：`tools/census_probe_py.py`（V1 首触分类 / V2 Session-Id 主体绑定 / V4 RFC 9728 元数据位；403 域名级≥80% 判 platform-firewall）。

## 目录

- `data/` 六批完整卷宗（b2-b7 各 n=1000）+ b1 150 样本 legacy 版
- `shards-b8/` b8 逐片原始数据（n=423）
- `results/` T0 汇总 + 趋势图 + 方法学 README-census-v1.0.md
- `tools/` 探针 + runner + 合并/对账/绘图脚本

## 口径

- b1 为 500 样本版历史已验收口径（34.57%/漂移 10.86%），legacy 150 版在 data/，完整归档补齐前 metadata 标注
- 分批计数经独立脚本七重对账（含 Wilson 双实现一致、分批和=6923）
- License：数据 CC0-1.0，代码 MIT
