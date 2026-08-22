# LLM 一对一自适应教学系统（MVP v0.1）

基于 LLM 的微积分一对一自适应教学系统。用户输入学习目标后，系统自动完成 **诊断 → 规划 → 教学 → 后测 → 状态更新** 的自适应闭环。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js 14 + TypeScript + Tailwind + Mermaid + KaTeX |
| 后端 | Python + FastAPI + SQLAlchemy + SymPy |
| LLM Runtime | OpenAI Agents SDK（无 Key 时自动降级为确定性引擎，闭环仍可跑通） |
| 数据库 | SQLite（开发）/ PostgreSQL（部署） |
| 接口 | REST + SSE（流式教学对话） |

## 核心流程

```
目标输入 → 诊断（≤6题）→ 路线规划 → 教学（对话+流式）→ 后测（3题）→ 更新掌握状态 → 下一节点 / 完成
```

### Session 状态机

`INIT → DIAGNOSIS → PLANNING → TEACHING → ASSESSMENT → REPLAN → TEACHING / COMPLETE`

### 5 个 Agent

| Agent | 职责 |
|---|---|
| KnowledgeMapAgent | 生成主题知识地图（DAG） |
| DiagnosticAgent | 生成诊断题 |
| PlannerAgent | 选择学习路径 |
| TutorAgent | 当前节点教学 |
| AssessmentAgent | 教学后测评 |

### Learner State 算法

- `mastery = 0.5*conceptual + 0.3*procedural + 0.2*transfer`
- 单题证据更新：`new = old * 0.65 + evidence * 0.35`
- 阈值：`<0.60 weak` · `0.60-0.79 developing` · `0.80-0.89 mastered` · `>=0.90 stable`

### Diagnostic Engine

- 节点评分：`score = uncertainty * importance * (1 + dependency)`
- 停止条件：答题 ≥ 6 题 / 3 个连续高置信节点 ≥ 0.80 / 下游被低掌握 prerequisite 阻断

## 目录结构

```
adaptive-tutor/
├─ backend/
│  ├─ main.py                 # FastAPI 入口（REST + SSE）
│  ├─ config.py               # 环境配置
│  ├─ database.py             # SQLAlchemy engine/session
│  ├─ models/                 # 9 张表 ORM 模型
│  ├─ agents/                 # 5 个 Agent + Provider（OpenAI / 确定性降级）
│  ├─ orchestration/
│  │  ├─ learning_loop.py     # 状态机编排
│  │  ├─ diagnostic_engine.py # 诊断引擎
│  │  └─ state_manager.py     # 状态读写与事件
│  ├─ services/
│  │  ├─ scoring.py           # 评分与 mastery 更新
│  │  ├─ verification.py      # SymPy 数学验证
│  │  └─ mermaid.py           # 知识地图 → Mermaid
│  ├─ schemas/                # Pydantic 结构化输出
│  ├─ seed/microcalculus.py   # 微积分种子地图 + 题库
│  └─ prompts/                # 5 个 Agent Prompt
├─ frontend/
│  ├─ app/                    # /start 与 /learn 页面
│  ├─ components/             # KnowledgeMap / QuizCard / Chat / Progress / Debug
│  └─ lib/                    # API 客户端（REST + SSE）
├─ tests/                     # 单元测试 + E2E（27 项）
└─ scripts/e2e_demo.py        # 全链路联调脚本
```

## 快速开始

### 1. 后端

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # 可选：填写 OPENAI_API_KEY
uvicorn main:app --reload   # http://localhost:8000
```

> 不配置 `OPENAI_API_KEY` 时自动使用确定性引擎（种子题库 + 规则），完整闭环可演示；
> 配置 Key 后自动切换 OpenAI Agents SDK 生成动态内容。

### 2. 前端

```bash
cd frontend
npm install
npm run dev                 # http://localhost:3000
```

### 3. 测试

```bash
python -m pytest tests/ -v  # 27 项测试
python scripts/e2e_demo.py  # 全链路联调（需后端已启动）
```

## API 一览

| Method | Path | 用途 |
|---|---|---|
| POST | `/api/learning/start` | 创建 session + 第一道诊断题 |
| GET | `/api/learning/{id}` | session 状态 |
| GET | `/api/learning/{id}/map` | 知识地图（Mermaid 数据） |
| POST | `/api/learning/{id}/answer` | 提交答案 |
| POST | `/api/learning/{id}/message` | 教学对话（SSE 流式） |
| POST | `/api/learning/{id}/start-assessment` | 启动后测 |
| GET | `/api/learning/{id}/progress` | 学习进度 |
| GET | `/api/learning/{id}/events` | 调试事件流 |

## 验收状态

- [x] Map：schema 正确、无环、边指向已有节点
- [x] Diagnostic：合法节点选择 + 停止条件
- [x] Scoring：评分一致 + mastery 公式正确
- [x] Math verification：SymPy 验证全部正确判定
- [x] Agent schema：确定性题库全部可解析
- [x] E2E：开始 → ≤6 题诊断 → 路线 → 教学 → 3 题后测 → 状态更新
- [x] Frontend smoke：答题、教学、地图、进度可用

## 生产部署提示

- 数据库切换：`DATABASE_URL=postgresql://user:pass@host/db`
- LLM：`LLM_PROVIDER=openai` + `OPENAI_API_KEY=...` + `OPENAI_MODEL=...`
- 前端构建：`npm run build && npm start`
