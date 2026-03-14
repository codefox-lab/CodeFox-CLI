<p align="center">
  <img src="https://raw.githubusercontent.com/URLbug/CodeFox-CLI/refs/heads/main/assets/logo.png" alt="CodeFox logo" width="120" />
</p>

<h1 align="center">CodeFox-CLI</h1>
<p align="center">
  Diff-aware AI code review for terminal and CI workflows
</p>

<p align="center">
  <a href="https://github.com/URLbug/CodeFox-CLI/actions?query=branch%3Amain"><img src="https://github.com/URLbug/CodeFox-CLI/workflows/CI/badge.svg" alt="CI" /></a>
  <a href="https://github.com/URLbug/CodeFox-CLI/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-green.svg" alt="Python 3.11+" /></a>
  <a href="https://github.com/codefox-lab/CodeFox-CLI/wiki"><img src="https://img.shields.io/badge/docs-Wiki-blue?logo=readme" alt="Wiki" /></a>
  <a href="https://pepy.tech/projects/codefox"><img src="https://static.pepy.tech/personalized-badge/codefox?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads" alt="PyPI Downloads"></a>
</p>

<p align="center">
  📚 <a href="https://github.com/codefox-lab/CodeFox-CLI/wiki">Documentation</a> •
  🚀 <a href="#-quick-start">Quick Start</a> •
  🐛 <a href="https://github.com/URLbug/CodeFox-CLI/issues">Report Issue</a> •
  📝 <a href="https://github.com/codefox-lab/Demo-PR-Action">Demo PRs</a>
</p>

---

## 🦊 Overview

**CodeFox-CLI** is a CLI-first AI code review tool for **git diffs, pull requests, and CI workflows**.

It analyzes code changes, retrieves relevant project context, and produces review feedback directly in the terminal or inside automated review pipelines.

CodeFox supports both:
- **local reviews with Ollama** for self-hosted workflows
- **cloud LLM providers** such as Gemini and OpenRouter when remote inference is preferred

It is designed for developers and teams who want a **CLI-first review workflow** for local checks, pull requests, and CI/CD pipelines.

---

## Why CodeFox?

- Reviews **git changes**, not just isolated files
- Uses **relevant codebase context** to improve review quality
- Works with **local or cloud models**
- Fits naturally into **terminal-based and CI workflows**
- Supports configurable review focus such as **security**, **performance**, and **style**

| Compared to linters | Compared to hosted AI reviewers |
|---|---|
| Reviews diffs with codebase context, not only static rules | Can run locally with Ollama |
| Can suggest fixes, not only flag issues | No hard vendor lock-in |
| Flexible review focus: security, performance, style | CLI-first workflow for local and CI usage |

<p align="center">
  <img src="https://raw.githubusercontent.com/URLbug/CodeFox-CLI/refs/heads/main/assets/work_review.gif" alt="CodeFox scan demo" width="800" />
</p>

---

## What CodeFox is and is not

CodeFox is a **CLI for automated AI review of git changes**.

It is **not** an IDE coding assistant like Cursor or Claude Code.  
It is built for **diff review workflows**, terminal usage, and CI/CD automation.

---

## Integrations

Current:
- GitHub Actions

Planned:
- GitLab
- Bitbucket

---

## Privacy

- With **Ollama**, reviews can run fully locally on your machine
- With **cloud providers**, code and context may be sent to external APIs depending on your configuration
- Use `.codefoxignore` to exclude files from analysis

---

## 📥 Installation

### For users

**uv**
```bash
uv tool install codefox
```

**pip**
```bash
python3 -m pip install codefox
```

---

## Verify installation

```bash
codefox version
```

---

## 🚀 Quick Start

1. Initialize CodeFox
```bash
codefox init
```

This stores your provider token locally and creates the initial config files.

2. Review your current git changes
```bash
codefox scan
```

What happens during `scan`:

- collects the current git diff

- loads relevant project context based on your configuration

- sends the review request to the configured model

- returns review comments and optional fix suggestions

3. Show version
```bash
codefox version
```

---

## ⚙️ Configuration

**Ignore file:** `./.codefoxignore`
Specifies paths that should not be uploaded to the File Store.

**Model settings:** `./.codefox.yml`
Used for fine-grained configuration of the analysis behavior and model parameters (such as model selection, temperature, review rules, baseline, and prompts).
For detailed configuration options and examples, see [**WIKI**](https://github.com/codefox-lab/CodeFox-CLI/wiki).

Example config used in the demo above (Ollama + qwen3-coder):

```yaml
provider: ollama
model:
  name: qwen3.5:9b
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

**Full configuration reference and examples:** [**WIKI**](https://github.com/codefox-lab/CodeFox-CLI/wiki) - provider settings, model options, review rules, prompts, and more.

---

## 🧩 Commands

| Command   | Description                                                                                          |
| --------- | ---------------------------------------------------------------------------------------------------- |
| `init`    | Saves the API key locally and creates a `.codefoxignore` and `.codefox.yml` file in the current directory.       |
| `list`    | Shows the full list of models available for the current provider (Gemini, Ollama, or OpenRouter) and embeddings (fastembed) from `.codefox.yml`. |
| `scan`    | Collects changes from the `git diff`, uploads files to the File Store, and sends requests to the configured model. |
| `version` | Displays the current CodeFox CLI version. |
| `clean` | Clears local cache used by CodeFox |
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
