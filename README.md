# 银行罚单挖掘与合规风险画像 Agent

爬取监管公示的银行罚单 → 结构化 → 分类归因 → 生成机构/责任人合规风险画像报告。
自研单 Agent(Harness 手写,不用框架): PE-R-R 大循环 + ToT 假设树 + 异步 HITL + 三级记忆。

设计文档见 `D:\software\kimi\kimi_data\复杂单Agent\design\`(阅读顺序见 handoff_M1.md)。

## 当前里程碑: M1 数据底座

范围(只许做这些):
1. 仓库骨架 + docker-compose 起本项目独立 PG+pgvector + alembic 迁移
2. `penalties / regulators / penalty_embeddings` 三表(字段照 data_schemas §1)
3. `penalty_crawler`: 金监总局本级爬取,快照留档,content_hash 去重
4. `penalty_parser`: LLM + Pydantic 契约抽取,校验失败重抽 ≤2 次
5. 控制层最小实现: 线性 Todo 执行器 + 四态 SkillResult 接口
6. 端到端冒烟: 爬 3 个月总局罚单 → 解析 → 入库

## 快速开始

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -e . -r requirements-dev.txt
cp .env.example .env        # 填入真实 LLM_API_KEY
docker compose -f deploy/docker-compose.yml up -d
alembic upgrade head
python scripts/smoke_m1.py  # 冒烟: 爬取→解析→入库
```
