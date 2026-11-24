# MCP Registry Security Census — 全量确权数据集 v1.0（T0 快照）

**确权主体**：王桂桂（Guigui Wang / Correctover）
**确权日期**：2026-11-24
**政府登记前置**：2026-11-23 上海市知识产权局数据产权登记「MCP生态安全暴露面与一致性故障判定基准数据集」已提交（审查中）——本包为该数据集的全量实测版本。

## 1. 数据集内容

官方 MCP registry（registry.modelcontextprotocol.io）声明 20,000 个 server 条目中实际探得 **6,923 个可达端点**，八批次全量安全普查快照（2026-11-24 T0）：

| 指标 | 数值 | Wilson 95% CI |
|---|---|---|
| 匿名可握手 / 可达端点 | 1,313/3,602 = **36.5%** | [34.9%, 38.0%] |
| 声明漂移（非 MCP 却声明为 MCP）/ 可达 | 465/3,602 = **12.9%** | [11.9%, 14.0%] |
| 正确认证挑战 / 可达 | 50.6% | — |
| blocked-403（服务端拒绝） | 1,289 | 单列，不入分母 |
| unreachable（不可达） | 1,936 | 单列，不入分母 |

**分层口径**（构成效应，单一快照会掩盖）：
- registry 前段（托管，b1/b2/b4/b5）：匿名率 35.0%，漂移 9.8%
- 自部署端点（b3）：匿名率 21.8%，漂移 13.6%
- registry 后段（b6/b7/b8）：匿名率 **44.6%**，漂移 17.8%
- 最新注册批次 b8（423 端点）：匿名率 **60.2%**——生态新增供给安全基线显著更低

## 2. 判定方法（可复现）

探针字段（V1-V4）：V1 首触分类（proper-auth-challenge / exposure / no-mcp / blocked-403 / unreachable）；V2 Session-Id 主体绑定（MCP 2025-06-18 规范 Session-as-Identity 缺陷）；V4 RFC 9728 资源元数据位。403 判定带 platform-firewall/server-auth 区分（域名级 403 率≥80% 判平台墙）。全部结果逐端点含原始 status 与 registry_claim_vs_reality 三元组。

## 3. 文件清单

- census-batch2..7-20261124.json：六批完整卷宗（各 n=1000，含逐端点结果）
- shards/b8-shard-01-part0..16.json：b8 逐片原始数据（n=423）
- census-batch1-20261124.json：b1 早期 150 端点样本（格式旧版，b1 完整口径以 500 样本版历史验收数字为准，随卷宗 metadata 标注）
- census-T0-20261124.json：全量加权汇总（含 trend_by_registration_order 与分层）
- trend-anon-20261124.png / trend-drift-20261124.png：趋势图（Wilson 误差棒）
- MANIFEST.sha256：全文件 sha256 清单（确权指纹）

## 4. 口径声明

- b1 为 500 样本版历史已验收口径（2026-11-24 上午验收：匿名 34.57%、漂移 10.86%），原始归档位置待补齐，metadata 已如实标注
- 分批计数均经独立脚本重算对账（七重验签），不接受任何中间脚本 summary 直接引用
- T+7 差分复测计划 2026-12-01 执行（本包为 T0 基线）

## 5. License

- 数据本体：CC0 1.0（vector data 不受版权约束口径）
- 判定方法/文档：MIT
