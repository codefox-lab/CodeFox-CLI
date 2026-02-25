# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities in public GitHub issues.**

If you believe you have found a security issue in CodeFox-CLI (e.g. secret leakage, unsafe handling of config or API keys, dependency vulnerability in our codebase, or a way to execute arbitrary code via the CLI), please report it privately:

- **Email:** [info@code-fox.online](mailto:info@code-fox.online)  
  Use a descriptive subject line (e.g. `[CodeFox-CLI] Security: brief description`).

### What to include

- Short description of the issue and impact.
- Steps to reproduce (or a minimal PoC), if possible.
- Your environment (OS, Python version, provider: Gemini/Ollama/OpenRouter).
- Whether you plan to disclose publicly and when (if applicable).

### What to expect

- We will acknowledge your report and aim to respond within **5 business days**.
- We will work with you to understand and fix the issue, and may ask for clarification.
- We will notify you when a fix is released and credit you in the release notes (unless you prefer to stay anonymous).
- We do not take legal action against researchers who report in good faith and follow responsible disclosure.

### Out of scope

- Issues in third-party services (Google Gemini, OpenRouter, Ollama) or their APIs.
- General security advice about code that *users* of CodeFox review with the tool (that is the tool’s purpose).
- Problems that require physical access, social engineering, or already-compromised machine.

## Security Practices for Users

- **Do not commit** `.codefoxenv` — it contains your API key. It is listed in `.gitignore`; ensure it stays ignored in your repo.
- Prefer **Ollama** or a self-hosted API if you do not want your code to leave your network.
- Keep **dependencies** up to date: `pip install -U codefox` (or reinstall from source).
- Run CodeFox only in environments you trust; the CLI reads your repo and sends content to the configured provider.

## Attribution

This security policy is inspired by common open-source security disclosure practices.
