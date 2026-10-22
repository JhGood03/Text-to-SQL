# SmartDataQuery · 智能数据查询系统

基于自然语言的数据仓库问答系统（Text-to-SQL）。用户用中文提问，系统自动完成元数据召回、SQL 生成与执行，并以流式方式返回执行进度和查询结果，无需掌握任何 SQL 语法。

---

## 目录

- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [项目结构](#项目结构)
- [工作原理](#工作原理)
- [接口说明](#接口说明)
- [元数据知识库构建](#元数据知识库构建)
- [本地调试](#本地调试)
- [常见问题](#常见问题)

---

## 核心特性

- **自然语言问数**：直接提问「统计各地区销量排行前三的商品」，自动生成并执行 SQL
- **多路语义召回**：字段、字段取值、业务指标三路并行召回，显著提升 Schema 定位准确率
- **元数据驱动**：以 MySQL 元数据为核心，配合向量索引与全文索引，让大模型「认识」你的数据仓库
- **生成-校验-纠错闭环**：SQL 生成后经 `EXPLAIN` 校验，失败则自动纠错重试
- **流式执行反馈**：SSE 实时推送 11 个节点的执行进度，前端进度条与结果表格同步更新
- **内置前端页面**：单文件、零外部依赖，与后端同源部署，无需额外构建
- **配置外置**：密码与密钥全部通过环境变量注入，仓库中不含任何敏感信息

---

## 系统架构

```
                        ┌──────────────────────────────┐
                        │        浏览器 / 前端          │
                        └──────────────┬───────────────┘
                                       │ POST /api/query (SSE)
                        ┌──────────────▼───────────────┐
                        │        FastAPI 服务层         │
                        │  路由 · 依赖注入 · 生命周期    │
                        └──────────────┬───────────────┘
                                       │
                        ┌──────────────▼───────────────┐
                        │      LangGraph 问数智能体     │
                        │         （12 个节点）         │
                        └──────────────┬───────────────┘
                                       │
        ┌──────────────────┬───────────┴───────────┬──────────────────┐
        │                  │                       │                  │
┌───────▼──────┐  ┌────────▼────────┐   ┌──────────▼────────┐  ┌──────▼───────┐
│    MySQL     │  │     Qdrant      │   │ Elasticsearch     │  │  Embedding   │
│  元数据+DW   │  │  字段/指标向量   │   │  字段取值全文索引  │  │  bge-large   │
└──────────────┘  └─────────────────┘   └───────────────────┘  └──────────────┘
                                       │
                              ┌────────▼────────┐
                              │   LLM (DeepSeek) │
                              └──────────────────┘
```

### 元数据知识库

系统的核心是「元数据知识库」，它为数据仓库提供语义层：

| 存储 | 内容 | 用途 |
|---|---|---|
| **MySQL `meta` 库** | `table_info`、`column_info`、`metric_info`、`column_metric` 四张表 | 完整的表结构、字段定义、业务指标口径 |
| **Qdrant** | `column_info_collection`、`metric_info_collection` | 字段与指标的语义向量索引，支撑自然语言召回 |
| **Elasticsearch** | `value_info` 索引（IK 中文分词） | 字段取值全文检索，支撑「华北」「手机数码」等实体匹配 |

---

## 技术栈

| 类别 | 选型 |
|---|---|
| 语言 | Python 3.12 |
| Web 框架 | FastAPI + Uvicorn（SSE 流式响应） |
| 工作流编排 | LangGraph |
| LLM 调用 | LangChain + DeepSeek |
| 关系型数据库 | MySQL 8 + SQLAlchemy 2.0（异步）+ asyncmy |
| 向量数据库 | Qdrant |
| 全文检索 | Elasticsearch 8 + IK 分词 |
| 文本嵌入 | bge-large-zh-v1.5（1024 维），TEI 部署 |
| 中文分词 | jieba |
| 配置管理 | OmegaConf + PyYAML + 环境变量 |
| 日志 | Loguru（支持 request_id 追踪） |

---

## 快速开始

### 1. 准备依赖服务

项目需要以下外部服务，建议用 Docker Compose 统一部署：

| 服务 | 默认端口 | 说明 |
|---|---|---|
| MySQL | 3306 | 存储元数据（`meta` 库）与数据仓库（`dw` 库） |
| Qdrant | 6333 | 向量数据库 |
| Elasticsearch | 9200 | 需安装 IK 中文分词插件 |
| Text Embeddings Inference | 8081 | 提供 bge-large-zh-v1.5 嵌入服务 |

> Elasticsearch 必须安装 IK 分词插件，否则 `value_info` 索引无法创建。

### 2. 安装项目依赖

```bash
git clone https://github.com/JhGood03/Text-to-SQL.git
cd Text-to-SQL

cd SmartDataQuery
uv sync
```

### 3. 配置环境变量

```bash
# 在仓库根目录执行
cp .env.example .env
```

然后编辑 `.env`，填入你的实际配置：

```ini
META_DB_HOST=127.0.0.1
META_DB_PORT=3306
META_DB_USER=root
META_DB_PASSWORD=your_password

DW_DB_HOST=127.0.0.1
DW_DB_PORT=3306
DW_DB_USER=root
DW_DB_PASSWORD=your_password

QDRANT_HOST=127.0.0.1
QDRANT_PORT=6333

EMBEDDING_HOST=127.0.0.1
EMBEDDING_PORT=8081
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1
EMBEDDING_API_KEY=EMPTY

ES_HOST=127.0.0.1
ES_PORT=9200

LLM_MODEL_NAME=deepseek-v4-flash
LLM_API_KEY=sk-your-key-here
LLM_BASE_URL=https://api.deepseek.com
```

> `.env` 已被 `.gitignore` 忽略，不会被提交到仓库。

### 4. 构建元数据知识库

首次运行前，需要把数据仓库的表结构、字段说明、指标定义同步到知识库：

```bash
cd SmartDataQuery
uv run python -m app.scripts.build_meta_knowledge -c app/conf/meta_config.yaml
```

该命令会依次完成：

1. 读取 `meta_config.yaml` 中定义的库表信息
2. 从数据仓库查询字段类型与示例取值，写入 MySQL `meta` 库
3. 对字段名、描述、别名建立 Qdrant 向量索引
4. 对标记 `sync: true` 的维度字段建立 Elasticsearch 全文索引
5. 对指标名称、描述、别名建立 Qdrant 向量索引

### 5. 启动服务

```bash
cd SmartDataQuery
uv run uvicorn main:app --host 127.0.0.1 --port 8000
```

打开浏览器访问 **http://127.0.0.1:8000/** 即可使用。

- 前端页面：http://127.0.0.1:8000/
- 接口文档：http://127.0.0.1:8000/docs

---

## 配置说明

### 配置加载机制

配置文件为 `SmartDataQuery/app/conf/app_config.yaml`，其中所有敏感项都写成 `${ENV_VAR:默认值}` 占位符：

```yaml
db_meta:
  host: ${META_DB_HOST:127.0.0.1}
  password: ${META_DB_PASSWORD:}
```

加载流程（`app/conf/app_config.py`）：

1. 读取仓库根目录的 `.env`（若存在），写入 `os.environ`
2. 用 PyYAML 解析 `app_config.yaml`（**不能用 OmegaConf 直接读**，否则 `${VAR}` 会被当成 OmegaConf 自身的插值语法而报错）
3. 递归替换所有 `${VAR}` 与 `${VAR:默认值}` 占位符
4. 与 dataclass schema 合并，做类型校验
5. 单例缓存，全局暴露为 `app_config`

### 元数据配置文件

`SmartDataQuery/app/conf/meta_config.yaml` 描述数据仓库的表与指标，是知识库构建的输入：

```yaml
tables:
  - name: dim_region
    role: dim
    description: 地区维度表
    columns:
      - name: region_name
        role: dimension
        description: 大区名称
        alias: [地区, 区域, 大区]
        sync: true          # true 表示该字段取值需建立全文索引

metrics:
  - name: GMV
    description: 成交金额总和
    relevant_columns:
      - fact_order.order_amount
    alias: [成交总额, 订单总额]
```

- `role` 取值：表为 `fact` / `dim`，字段为 `primary_key` / `foreign_key` / `measure` / `dimension`
- `sync: true` 仅对维度字段有意义，表示把该字段的去重取值同步到 Elasticsearch

---

## 项目结构

```
Text-to-SQL/
├── .env.example                    # 环境变量模板
├── .gitignore
├── README.md
└── SmartDataQuery/
    ├── main.py                     # FastAPI 入口（路由注册、中间件、静态挂载）
    ├── pyproject.toml              # 依赖声明
    ├── static/
    │   └── index.html              # 单文件前端页面（零依赖）
    ├── prompts/                    # 提示词模板（7 个）
    │   ├── extend_keywords_for_column_recall.prompt
    │   ├── extend_keywords_for_value_recall.prompt
    │   ├── extend_keywords_for_metric_recall.prompt
    │   ├── filter_table_info.prompt
    │   ├── filter_metric_info.prompt
    │   ├── generate_sql.prompt
    │   └── correct_sql.prompt
    └── app/
        ├── agtent/                 # 问数智能体
        │   ├── graph.py            # LangGraph 图定义
        │   ├── state.py            # 全局状态定义
        │   ├── context.py          # 运行时依赖上下文
        │   ├── llm.py              # LLM 初始化
        │   └── nodes/              # 12 个节点
        ├── api/                    # 接口层
        │   ├── dependencies.py     # 依赖注入
        │   ├── routers/            # 路由
        │   └── schemas/            # 请求/响应模型
        ├── clients/                # 外部服务客户端管理器
        ├── conf/                   # 配置类与配置文件
        ├── core/                   # 日志、生命周期、请求上下文
        ├── entities/               # 业务实体（DTO）
        ├── models/                 # SQLAlchemy ORM 模型
        ├── repositories/           # 数据访问层
        │   ├── es/                 # Elasticsearch 仓储
        │   ├── mysql/dw/           # 数据仓库仓储
        │   ├── mysql/meta/         # 元数据仓储（含 mappers）
        │   └── qdrant/             # 向量库仓储
        ├── scripts/                # 知识库构建入口
        ├── services/               # 业务服务层
        └── utils/                  # 工具（提示词加载）
```

---

## 工作原理

### 工作流

问数智能体由 12 个节点组成，`extract_keywords` 之后三路召回并行执行：

```
START
  │
  ▼
extract_keywords ──┬──► recall_column ──┐
                   ├──► recall_value  ──┼──► merge_retrieved_info
                   └──► recall_metric ──┘            │
                                                     ├──► filter_table ──┐
                                                     └──► filter_metric ─┴──► add_extra_context
                                                                                    │
                                                                                    ▼
                                                                              generate_sql
                                                                                    │
                                                                                    ▼
                                                                              validate_sql
                                                                               │         │
                                                                    error=None │         │ error≠None
                                                                               ▼         ▼
                                                                          execute_sql ◄── correct_sql
                                                                               │
                                                                               ▼
                                                                              END
```

### 各节点职责

| 节点 | 职责 |
|---|---|
| `extract_keywords` | 用 jieba 按词性抽取关键词，并附加完整原句兜底 |
| `recall_column` | LLM 扩展字段关键词 → 向量化 → Qdrant 检索字段 |
| `recall_value` | LLM 扩展取值候选 → Elasticsearch 全文检索字段取值 |
| `recall_metric` | LLM 扩展指标关键词 → 向量化 → Qdrant 检索指标 |
| `merge_retrieved_info` | 合并三路结果：补指标关联字段、补取值示例、按表分组、显式补齐主外键 |
| `filter_table` | LLM 从候选表中裁剪出必需的表与字段 |
| `filter_metric` | LLM 从候选指标中筛选出必需指标 |
| `add_extra_context` | 注入当前日期信息与数据仓库版本/方言 |
| `generate_sql` | 结合表结构、指标口径、日期、方言生成 SQL |
| `validate_sql` | 用 `EXPLAIN` 校验 SQL 可执行性 |
| `correct_sql` | 根据数据库报错信息做最小必要修复 |
| `execute_sql` | 在数据仓库执行 SQL，流式推送结果 |

### 提示词调优要点

`generate_sql.prompt` 与 `filter_table_info.prompt` 中有几条针对实际效果调优的规则，改动时需注意：

- **必须 JOIN 维表输出名称**：事实表通常只有 `region_id`，但用户要看「华东」而非「R005」，因此要求生成 SQL 时关联维表并输出 `region_name`
- **分组粒度须与业务语义一致**：`region_name` 可能一名多 ID（如「华东」对应浙江、上海两个 `region_id`），按名称分区才能得到正确的「各地区」统计
- **实体名称字段必须保留**：过滤表时若只保留 ID 字段，结果无法阅读，因此要求选中实体时一并保留其名称字段

---

## 接口说明

### POST /api/query

接收自然语言查询，以 SSE（Server-Sent Events）流式返回执行进度与结果。

**请求**

```http
POST /api/query
Content-Type: application/json

{
  "query": "统计各地区销量排行前三的商品"
}
```

**响应**　`Content-Type: text/event-stream`

进度事件（每个节点发送 `running` 与 `success`/`error` 两条）：

```json
{"type": "progress", "step": "召回字段", "status": "running"}
{"type": "progress", "step": "召回字段", "status": "success"}
```

结果事件：

```json
{
  "type": "result",
  "data": [
    {"region_name": "华东", "product_name": "奥利奥巧克力夹心饼干", "total_quantity": "100"},
    {"region_name": "华东", "product_name": "蒙牛纯牛奶 250ml*12", "total_quantity": "45"}
  ]
}
```

错误事件：

```json
{"type": "error", "message": "数据库连接超时"}
```

各帧之间以 `\n\n` 分隔。响应头包含 `X-Request-ID`，可用于日志追踪。

**进度步骤取值**：`抽取关键字`、`召回字段`、`召回指标`、`召回字段取值`、`合并召回信息`、`过滤指标`、`过滤表格`、`添加额外上下文信息`、`生成 SQL`、`验证 SQL`、`执行 SQL`

### 其他路由

| 路由 | 说明 |
|---|---|
| `GET /` | 前端页面 |
| `GET /docs` | Swagger 交互式文档 |
| `GET /static/*` | 静态资源 |

---

## 元数据知识库构建

若数据仓库的表结构或指标定义发生变化，需重新执行构建：

```bash
cd SmartDataQuery
uv run python -m app.scripts.build_meta_knowledge -c app/conf/meta_config.yaml
```

**注意事项**

- MySQL 中的元数据使用 `merge` 写入，重复执行是幂等的
- Qdrant 使用随机 UUID 作为 point id，**重复执行会产生重复向量**，重建前建议先删除原有 collection
- Elasticsearch 的 `value_info` 索引中，文档 ID 为 `表名.字段名.取值`，重复写入是幂等的

---

## 本地调试

### 直接运行智能体

不启动 Web 服务，直接跑通整条链路并打印每个事件的输出：

```bash
cd SmartDataQuery
uv run python -m app.agtent.graph
```

在 `app/agtent/graph.py` 的 `if __name__ == '__main__':` 代码块中修改 `state = DataAgentState(query="...")` 即可更换问题。

### 单独测试外部服务连接

各客户端管理器文件末尾都带有测试入口，可直接运行：

```bash
uv run python -m app.clients.mysql_client_manager      # 测试 MySQL
uv run python -m app.clients.embedding_client_manager  # 测试 Embedding
uv run python -m app.clients.es_client_manager         # 测试 Elasticsearch
```

---

## 常见问题

**Q：启动时报错 `UnsupportedInterpolationType`**

配置文件中的 `${VAR}` 与 OmegaConf 的插值语法冲突。项目已改为用 PyYAML 读取配置文件，若手动改过 `app_config.py` 请确认使用的是 `yaml.safe_load` 而非 `OmegaConf.load`。

**Q：查询时提示 embedding 服务连接失败**

检查 `EMBEDDING_BASE_URL` 是否可达，且服务返回的是 1024 维向量（`bge-large-zh-v1.5`）。维度不匹配会导致 Qdrant 检索失败。

**Q：Elasticsearch 报 `unknown analyzer [ik_max_word]`**

未安装 IK 分词插件。需要重新构建 ES 镜像，把 `elasticsearch-analysis-ik` 插件安装到 `/usr/share/elasticsearch/plugins`。

**Q：Qdrant 提示版本不兼容**

`qdrant-client` 与 Qdrant 服务端版本差异过大时会出现警告。主版本保持一致、次版本相差不超过 1 即可，不影响功能。

**Q：生成的 SQL 只返回 ID 没有名称**

检查 `filter_table_info.prompt` 中「实体名称字段必须保留」与 `generate_sql.prompt` 中「必须 JOIN 维表」这两条规则是否被误删。

**Q：`api_key` 为空的报错**

确认已在 `.env` 中填写 `LLM_API_KEY`，且 `.env` 位于仓库根目录（与 `.gitignore` 同级）。

---

## 许可

本项目仅供学习与研究使用。
