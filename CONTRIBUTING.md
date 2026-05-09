# Contributing to FlowAgent

FlowAgent is a small personal project. Contributions are welcome, but the project is still experimental, so keep changes focused and easy to review.

## Getting Started

```bash
git clone https://github.com/IntelFortis/flowagent.git
cd flowagent

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e ".[dev,ui]"
```

On macOS or Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

## Making Changes

- Open an issue or keep the pull request description clear if the change is more than a small fix.
- Keep unrelated refactors out of feature or bug-fix changes.
- Add or update tests when behavior changes.
- Update `README.md` or examples when the user-facing workflow changes.

## Tests

Run the Python tests:

```bash
pytest
```

Build the frontend:

```bash
cd web
npm install
npm run build
```

## Pull Requests

Before opening a pull request, check:

- The change is scoped to one topic.
- Tests pass locally where practical.
- New public claims in documentation are backed by the code.
- No secrets, local credentials, logs, generated caches, or personal files are included.

## Releases

There is no automated PyPI release process in this repository. Version numbers and release notes should be updated manually when a real release is prepared.
