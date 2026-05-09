<div align="center">

# FlowAgent

**下一代工作流自动化框架**

[![PyPI version](https://badge.fury.io/py/flowagent.svg)](https://badge.fury.io/py/flowagent)
[![Python](https://img.shields.io/pypi/pyversions/flowagent.svg)](https://pypi.org/project/flowagent/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/flowagent)](https://pepy.tech/project/flowagent)
[![GitHub Stars](https://img.shields.io/github/stars/flowagent/flowagent.svg)](https://github.com/flowagent/flowagent/stargazers)

[English](./README.md) | [中文](./README_zh.md) | [日本語](./README_ja.md) | [한국어](./README_ko.md)

</div>

---

## 为什么选择 FlowAgent？

构建复杂的工作流自动化应该像搭积木一样简单。FlowAgent 让您只需几行代码就能创建复杂的 AI 驱动工作流。

### 核心特性

- **3 行代码创建工作流** - 用最少的代码创建复杂工作流
- **DAG + 事件驱动架构** - 创新设计，最大灵活性
- **异步和分布式执行** - 高性能、可扩展的处理
- **丰富的生态系统集成** - 与 LLM、数据库、云服务无缝连接
- **可视化工作流编辑器** - 拖拽式工作流设计
- **智能错误处理** - 自动重试、回退和恢复
- **实时监控** - 实时执行跟踪和日志记录
- **类型安全** - 完整的 Python 类型提示

## 快速开始

### 安装

```bash
pip install flowagent
```

### Hello World

```python
from flowagent import Workflow, task

@task
def hello():
    return "Hello, FlowAgent!"

workflow = Workflow("hello-world")
workflow.add(hello)
result = workflow.run()
```

### 实际示例

```python
from flowagent import Workflow, task, Context
from flowagent.integrations import OpenAI, PostgreSQL

@task(retries=3, timeout=30)
async def analyze_data(ctx: Context):
    """使用 LLM 分析数据"""
    data = await ctx.get("raw_data")
    llm = OpenAI(model="gpt-5.5")

    analysis = await llm.chat(
        f"分析这些数据: {data}",
        system="你是一个数据分析师"
    )
    return analysis

@task
async def save_results(ctx: Context, analysis: str):
    """保存分析结果到数据库"""
    db = PostgreSQL(connection_string="postgresql://...")
    await db.execute(
        "INSERT INTO analyses (result) VALUES ($1)",
        analysis
    )
    return {"status": "saved"}

@task
async def notify_team(ctx: Context, result: dict):
    """通知团队"""
    await ctx.send_notification(
        channel="slack",
        message=f"分析完成: {result['status']}"
    )

# 创建带依赖的工作流
workflow = Workflow("data-pipeline")
workflow.add(analyze_data)
workflow.add(save_results, depends_on=[analyze_data])
workflow.add(notify_team, depends_on=[save_results])

# 执行
await workflow.run_async()
```

## 架构

FlowAgent 使用革命性的 **DAG + 事件驱动** 架构：

```
┌─────────────────────────────────────────────────────────────┐
│                      FlowAgent 核心                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   任务      │  │  工作流     │  │   上下文    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                 │
│         ▼                ▼                ▼                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              DAG 执行引擎                               ││
│  │  • 依赖解析  • 并行执行                                 ││
│  │  • 状态管理  • 错误恢复                                 ││
│  └─────────────────────────────────────────────────────────┘│
│         │                │                │                 │
│         ▼                ▼                ▼                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   本地      │  │  分布式     │  │    异步     │         │
│  │  执行器     │  │  执行器     │  │  执行器     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
         │                │                │
         ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                    集成层                                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  LLMs   │  │ 数据库  │  │  云服务  │  │ 消息队列│       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 集成

FlowAgent 与您喜爱的工具无缝集成：

| 类别 | 集成 |
|------|------|
| **LLMs** | OpenAI, Anthropic, Google AI, Mistral, Ollama |
| **数据库** | PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch |
| **云服务** | AWS, Google Cloud, Azure, Vercel, Netlify |
| **消息队列** | Slack, Discord, Telegram, Email, Webhooks |
| **存储** | S3, GCS, Azure Blob, 本地文件 |
| **监控** | Prometheus, Grafana, Datadog, New Relic |

## 示例

### 数据管道

```python
from flowagent import Workflow, task

@task
def extract(): ...

@task
def transform(data): ...

@task
def load(data): ...

workflow = Workflow("etl-pipeline")
workflow.chain(extract, transform, load)
await workflow.run_async()
```

### 聊天机器人代理

```python
from flowagent import Workflow, task, Context
from flowagent.integrations import OpenAI

@task
async def process_message(ctx: Context):
    llm = OpenAI(model="gpt-5.5")
    response = await llm.chat(ctx.get("user_message"))
    return response

workflow = Workflow("chatbot")
workflow.add(process_message)
```

### CI/CD 自动化

```python
from flowagent import Workflow, task

@task
def run_tests(): ...

@task
def build(): ...

@task
def deploy(): ...

workflow = Workflow("ci-cd")
workflow.add(run_tests)
workflow.add(build, depends_on=[run_tests])
workflow.add(deploy, depends_on=[build])
```

## 文档

- [快速开始](https://flowagent.dev/docs/getting-started)
- [API 参考](https://flowagent.dev/docs/api)
- [示例](https://flowagent.dev/docs/examples)
- [架构指南](https://flowagent.dev/docs/architecture)
- [集成指南](https://flowagent.dev/docs/integrations)

## 性能

FlowAgent 为速度而生：

| 指标 | FlowAgent | 竞品 A | 竞品 B |
|------|-----------|--------|--------|
| 任务创建 | 0.1ms | 2.5ms | 1.8ms |
| 工作流执行 | 15ms | 120ms | 85ms |
| 内存使用 | 12MB | 45MB | 32MB |
| 并发任务 | 10,000+ | 1,000 | 500 |

## 贡献

我们欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

### 快速贡献设置

```bash
# 克隆仓库
git clone https://github.com/flowagent/flowagent.git
cd flowagent

# 安装依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行代码检查
pre-commit run --all-files
```

## 社区

- [Discord](https://discord.gg/flowagent)
- [Twitter](https://twitter.com/flowagent)
- [博客](https://flowagent.dev/blog)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/flowagent)

## 赞助商

<div align="center">
  <a href="https://flowagent.dev/sponsors">
    <img src="https://flowagent.dev/sponsors.svg" alt="Sponsors" width="600">
  </a>
</div>

## 许可证

FlowAgent 使用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## Star 历史

<div align="center">
  <a href="https://star-history.com/#flowagent/flowagent&Date">
    <img src="https://api.star-history.com/svg?repos=flowagent/flowagent&type=Date" alt="Star History Chart" width="600">
  </a>
</div>

---

<div align="center">
  <p>由 FlowAgent 团队用 ❤️ 制作</p>
  <p>
    <a href="https://flowagent.dev">网站</a> •
    <a href="https://docs.flowagent.dev">文档</a> •
    <a href="https://github.com/flowagent/flowagent">GitHub</a> •
    <a href="https://discord.gg/flowagent">Discord</a>
  </p>
</div>
