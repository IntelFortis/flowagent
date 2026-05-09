# FlowAgent

FlowAgent 是一个个人写的 Python 工作流自动化实验项目，带一个 React 可视化编辑器。

它更适合作为学习项目、本地原型，或者继续改造的基础。它不是成熟产品，也不应该被当作已经稳定发布的生产级框架。

## 当前状态

- 个人实验项目
- 这个仓库没有发布到 PyPI
- 没有公开、可信的性能基准
- 不承诺生产环境可用性
- API 和数据结构后续可能继续变化

## 目前包含什么

- 基于 `Workflow`、`@task`、`Context`、`State` 的 Python 工作流核心
- 基础 DAG 任务依赖
- 同步和异步执行
- 用于可视化编辑器的 FastAPI 后端
- React/Vite 写的可视化工作流编辑器
- 一些内置节点执行器，比如 HTTP 请求、JSON 处理、过滤、代码片段、文件/日志输出、简单 AI 类节点
- 一些可选的 LLM、数据库、云服务和消息集成封装

部分集成模块需要额外依赖和外部服务。使用前最好按自己的场景重新检查和测试。

## 重要说明

- 本地 API 层的工作流数据目前是内存存储。
- 可视化编辑器主要用于本地开发和实验。
- 代码执行节点不是安全沙箱。
- 条件分支能力还比较有限。
- 这个项目没有做过生产安全审计。

## 快速开始

克隆仓库：

```bash
git clone https://github.com/IntelFortis/flowagent.git
cd flowagent
```

创建虚拟环境并本地安装：

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e ".[ui]"
```

最小示例：

```python
from flowagent import Workflow, task


@task
def hello():
    return "Hello, FlowAgent!"


workflow = Workflow("hello-world")
workflow.add(hello)

print(workflow.run())
```

保存为 `hello.py` 后运行：

```bash
flowagent run hello.py
```

## 可视化编辑器

启动本地 API 和打包后的 UI：

```bash
flowagent ui
```

然后打开：

```text
http://localhost:8000
```

前端开发模式：

```bash
cd web
npm install
npm run dev
```

## 项目结构

```text
flowagent/
  core/          Python 工作流核心
  integrations/ 可选服务集成
  server/        FastAPI API 和打包后的静态 UI
  visualizer/    HTML 可视化辅助代码
web/             React/Vite 可视化编辑器源码
examples/        示例工作流
tests/           Python 测试
```

## 开发

安装开发依赖：

```bash
pip install -e ".[dev,ui]"
```

运行 Python 测试：

```bash
pytest
```

构建前端：

```bash
cd web
npm install
npm run build
```

## 许可证

本项目使用 MIT License，见 [LICENSE](LICENSE)。

Made by IntelFortis.
