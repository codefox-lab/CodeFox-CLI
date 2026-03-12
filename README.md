<p align="center">
  <img src="https://raw.githubusercontent.com/URLbug/CodeFox-CLI/refs/heads/main/assets/logo.png" alt="CodeFox logo" width="120" />
</p>

<h1 align="center">CodeFox-CLI</h1>
<p align="center">
    Intelligent automated code review system
</p>

<p align="center">
  <a href="https://github.com/URLbug/CodeFox-CLI/actions?query=branch%3Amain"><img src="https://github.com/URLbug/CodeFox-CLI/workflows/CI/badge.svg" alt="CI" /></a>
  <a href="https://github.com/URLbug/CodeFox-CLI/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-green.svg" alt="Python 3.11+" /></a>
  <a href="https://github.com/URLbug/CodeFox-CLI/blob/main/WIKI.md"><img src="https://img.shields.io/badge/docs-WIKI-blue?logo=readme" alt="Wiki" /></a>
  <a href="https://pepy.tech/projects/codefox"><img src="https://static.pepy.tech/personalized-badge/codefox?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads" alt="PyPI Downloads"></a>
</p>


## 🦊 Overview

**CodeFox-CLI** is an intelligent automated code review system that takes over routine security and code quality checks, allowing senior developers to focus on architecture and complex tasks.

Unlike traditional linters, CodeFox understands the context of the entire project and its business logic, delivering not just review comments but **ready-to-apply fixes** (Auto-Fix). Works with **Gemini**, **Ollama**, and **OpenRouter** - use your preferred AI backend.

| vs Linters | vs AI code review (e.g. CodeRabbit) |
|------------|-------------------------------------|
| Understands full project context & business logic | Self-hosted / local (Ollama), no vendor lock-in |
| Suggests fixes, not only rules | Configurable models, security/performance/style rules |
| RAG over your codebase for relevant hints | CLI-first: `git diff` → review in seconds |

<p align="center">
  <img src="https://raw.githubusercontent.com/URLbug/CodeFox-CLI/refs/heads/main/assets/work_review.gif" alt="CodeFox scan demo" width="800" />
</p>

---

## 📥 Installation

Choose the installation method that fits your workflow.

### 🔹 Install dependencies (local setup)

```bash
pip install -r requirements.txt
```
### 🔹 Development mode (editable install)

Provides the local codefox CLI command and enables live code changes.

```bash
python3 -m pip install -e .
```

### 🔹 Install from GitHub

🐍 Using pip

```bash
python3 -m pip install codefox
# or python3 -m pip install git+https://github.com/URLbug/CodeFox-CLI.git@main
```

⚡ Using uv (recommended for CLI usage)
```bash
uv tool install codefox
# or uv tool install git+https://github.com/URLbug/CodeFox-CLI.git@main
```

---

✅ Verify installation
```bash
codefox version
```
Or
```bash
python3 -m codefox version
```

## 🚀 Quick Start

### Initialize (stores your API key)

```bash
codefox init
```

### Run a scan (uses the current git diff)

```bash
codefox scan
```

### Show version

```bash
codefox version
```

---

## ⚙️ Configuration

**Ignore file:** `./.codefoxignore`
Specifies paths that should not be uploaded to the File Store.

**Model settings:** `./.codefox.yml`
Used for fine-grained configuration of the analysis behavior and model parameters (such as model selection, temperature, review rules, baseline, and prompts).
For detailed configuration options and examples, see [**WIKI.md**](WIKI.md).

Example config used in the demo above (Ollama + qwen3-coder):

```yaml
provider: ollama
model:
  name: qwen3-coder:30b
  temperature: 0.5
  max_tokens: 4000
review:
  severity: high
  max_issues: null
  suggest_fixes: true
  diff_only: false
baseline:
  enable: true
ruler:
  security: true
  performance: true
  style: true
prompt:
  system: null
  extra: null
```

**Token configuration:** `./codefoxenv`
Stores the API token for the model. This file is used by the CLI for authentication and should not be committed to version control.

---

## 📚 Documentation

**Full configuration reference and examples:** [**WIKI.md**](https://github.com/URLbug/CodeFox-CLI/blob/main/WIKI.md) - provider settings, model options, review rules, prompts, and more.

---

## 🧩 Commands

| Command   | Description                                                                                          |
| --------- | ---------------------------------------------------------------------------------------------------- |
| `init`    | Saves the API key locally and creates a `.codefoxignore` and `.codefox.yml` file in the current directory.       |
| `list`    | Shows the full list of models available for the current provider (Gemini, Ollama, or OpenRouter) from `.codefox.yml`. |
| `scan`    | Collects changes from the `git diff`, uploads files to the File Store, and sends requests to the configured model. |
| `version` | Displays the current CodeFox CLI version.                                                            |
| `--help`  | Shows available flags and usage information.                                                         |

---

## 🧪 Examples

### List available models (for the provider in `.codefox.yml`)

```bash
codefox list
```

### Run a scan in a project

```bash
codefox scan
```

---

## 🛠 Development

Install with dev dependencies (includes pytest, mypy, ruff, types-PyYAML):

**pip:**
```bash
pip install -e ".[dev]"
# or: pip install -r requirements.txt -r requirements-dev.txt
```

**uv:**
```bash
uv pip install -e ".[dev]"
```

Run tests:

```bash
pytest tests -v
```

Lint and format:

```bash
ruff check codefox tests
ruff format codefox tests
```

Static type check:

```bash
mypy codefox
```

---

## 🤝 Contributing

Bug reports, pull requests, and documentation improvements are welcome.
