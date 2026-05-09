# FlowAgent

FlowAgent is a small personal Python workflow automation experiment with a visual React editor.

It is useful as a learning project, a prototype, or a base for local workflow ideas. It is not a mature production product, and the API should be treated as unstable.

## Current Status

- Personal/experimental project
- Not published to PyPI by this repository
- No published performance benchmark
- No production deployment guarantee
- Interfaces and data formats may change

## What Is Included

- A Python workflow core built around `Workflow`, `@task`, `Context`, and `State`
- Basic DAG-style task dependencies
- Sync and async workflow execution
- A FastAPI backend for the visual editor
- A React/Vite visual workflow editor
- Built-in node executors for HTTP requests, JSON transforms, filters, code snippets, file/log output, and simple AI-style nodes
- Optional integration wrappers for LLMs, databases, cloud services, and messaging

Some integration modules require optional dependencies and external services. They should be reviewed and tested for your own use case before relying on them.

## Important Caveats

- Workflow data is stored in memory in the local API layer.
- The visual editor is mainly for local development and experimentation.
- The code execution node is not a secure sandbox.
- Branching and condition handling are still limited.
- The project has not been audited for production security.

## Quick Start

Clone the repository:

```bash
git clone https://github.com/IntelFortis/flowagent.git
cd flowagent
```

Create a virtual environment and install the package locally:

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e ".[ui]"
```

Run a minimal workflow:

```python
from flowagent import Workflow, task


@task
def hello():
    return "Hello, FlowAgent!"


workflow = Workflow("hello-world")
workflow.add(hello)

print(workflow.run())
```

Save it as `hello.py`, then run:

```bash
flowagent run hello.py
```

## Visual Editor

Start the local API and bundled UI:

```bash
flowagent ui
```

Then open:

```text
http://localhost:8000
```

For frontend development:

```bash
cd web
npm install
npm run dev
```

## Project Layout

```text
flowagent/
  core/          Python workflow primitives
  integrations/ Optional service wrappers
  server/        FastAPI API and bundled static UI
  visualizer/    HTML visualizer helpers
web/             React/Vite visual editor source
examples/        Example workflows and demos
tests/           Python tests
```

## Development

Install development dependencies:

```bash
pip install -e ".[dev,ui]"
```

Run Python tests:

```bash
pytest
```

Build the frontend:

```bash
cd web
npm install
npm run build
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

Made by IntelFortis.
