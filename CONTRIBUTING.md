# Contributing to FlowAgent

Thank you for your interest in contributing to FlowAgent! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a new branch for your feature or bug fix
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip or poetry
- Git

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/flowagent.git
cd flowagent

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### IDE Setup

We recommend using VS Code with the following extensions:
- Python
- Pylance
- Ruff
- MyPy

## Making Changes

### Branch Naming

- Feature: `feature/description`
- Bug fix: `fix/description`
- Documentation: `docs/description`
- Refactor: `refactor/description`

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Refactoring
- `test`: Adding tests
- `chore`: Maintenance

Example:
```
feat(workflow): add parallel execution support

Add support for running tasks in parallel using asyncio.gather.
This improves performance for independent tasks.

Closes #123
```

### Code Style

We use:
- [Ruff](https://github.com/astral-sh/ruff) for linting
- [MyPy](https://mypy-lang.org/) for type checking
- [Black](https://github.com/psf/black) for formatting (optional)

Run linting:
```bash
ruff check .
```

Run type checking:
```bash
mypy flowagent
```

Format code:
```bash
ruff format .
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=flowagent --cov-report=html

# Run specific test file
pytest tests/test_workflow.py

# Run tests matching pattern
pytest -k "test_parallel"
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names
- Test both success and failure cases
- Use fixtures for common setup

Example:
```python
import pytest
from flowagent import Workflow, task

@pytest.fixture
def sample_workflow():
    @task
    def hello():
        return "Hello"

    workflow = Workflow("test")
    workflow.add(hello)
    return workflow

def test_workflow_execution(sample_workflow):
    results = sample_workflow.run()
    assert "hello" in results
    assert results["hello"] == "Hello"

def test_workflow_with_dependencies():
    @task
    def first():
        return 1

    @task
    def second(ctx):
        return ctx.get("dep:first") + 1

    workflow = Workflow("test")
    workflow.add(first)
    workflow.add(second, depends_on=[first])

    results = workflow.run()
    assert results["second"] == 2
```

## Documentation

### Building Docs

```bash
# Install documentation dependencies
pip install -e ".[dev]"

# Build documentation
mkdocs build

# Serve documentation locally
mkdocs serve
```

### Writing Documentation

- Use Markdown format
- Include code examples
- Keep documentation up-to-date with code changes
- Add docstrings to all public functions and classes

## Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Update the changelog
5. Request review from maintainers

### PR Checklist

- [ ] Code follows the project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Changelog updated

## Release Process

1. Update version in `pyproject.toml` and `flowagent/__init__.py`
2. Update CHANGELOG.md
3. Create a release branch
4. Run full test suite
5. Create a GitHub release
6. Publish to PyPI

## Questions?

Feel free to ask questions in:
- [GitHub Discussions](https://github.com/flowagent/flowagent/discussions)
- [Discord](https://discord.gg/flowagent)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/flowagent)

Thank you for contributing to FlowAgent!
