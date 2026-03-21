# ⚠️ Documentation Notice

This file is **no longer the primary documentation source**.

The **official and actively maintained documentation** has been moved to the GitHub Wiki:

👉 https://github.com/codefox-lab/CodeFox-CLI/wiki

Please refer to the Wiki for:

- installation guides
- configuration reference
- CLI commands
- GitHub Actions integration
- examples and usage guides

The Wiki allows documentation to be updated independently from the main repository and provides better navigation across pages, which is a common approach used in many GitHub projects. :contentReference[oaicite:0]{index=0}

---

## Quick Links

- 📖 **Documentation Home**  
  https://github.com/codefox-lab/CodeFox-CLI/wiki

- ⚙️ **Configuration Guide**  
  https://github.com/codefox-lab/CodeFox-CLI/wiki/Configurations

- 💻 **CLI Commands**  
  https://github.com/codefox-lab/CodeFox-CLI/wiki/CLI-commands

- 🚀 **GitHub Actions**  
  https://github.com/codefox-lab/CodeFox-CLI/wiki/GitHub-Action

---

# ⚙️ `.codefox.yml` Configuration

The `.codefox.yml` file allows you to configure the analysis behavior, model selection, review format, and the AI provider (Gemini, Ollama, OpenRouter).

All parameters are optional except `model` and `model.name`.

---

## 🔌 `provider`

**Type:** `string`  
**Default:** `gemini`  
**Description:** The AI provider used for code analysis and (for some providers) embeddings.

Supported values:

| Value        | Description |
| ------------ | ----------- |
| `gemini`     | Google Gemini API (default). Requires API key in `.codefoxenv`. |
| `ollama`     | Local or remote Ollama server. RAG uses the configured embedding model. |
| `openrouter` | OpenRouter API (many models). Uses embeddings for RAG context. |

Example:

```yaml
provider: ollama
```

---

## 🧠 `model`

Settings for the LLM being used.

```yaml
model:
  name: gemini-3-flash-preview
  temperature: 0.2
  max_tokens: 4000
  max_completion_tokens: null
  timeout: 600
  # Provider-specific (Ollama / OpenRouter):
  base_url: null
  embedding: null
```

### `model.name`

**Type:** `string`
**Description:** The name of the model used for code analysis.

Examples:

```yaml
name: gemini-3-flash-preview
name: gemini-3-pro-preview
name: gemini-3-pro
```

---

### `model.temperature`

**Type:** `number`
**Default:** `0.2`

Controls the creativity level of the model.

Recommendations:

* `0.0 – 0.2` -> deterministic and stable analysis ✅
* `0.3 – 0.7` -> more “conversational” suggestions
* `> 0.7` -> ❌ not recommended for code review

---

### `model.max_tokens`

**Type:** `number | null`
**Default:** `4000`

Limits the maximum size of the model’s response.

* `null` -> the model’s default limit is used
* number -> hard limit

Example:

```yaml
max_tokens: 3000
```

---

### `model.max_completion_tokens`

**Type:** `number | null`  
**Default:** `null`

Separate limit for completion tokens (used by OpenRouter and some APIs). If `null`, the provider default or `max_tokens` is used.

---

### `model.timeout`

**Type:** `number`  
**Default:** `600`

Request timeout in seconds for API calls.

---

### `model.base_url`

**Type:** `string | null`  
**Relevant for:** `ollama`, `openrouter`

Overrides the default API base URL.

* **Ollama:** default `https://ollama.com`. Set to your Ollama host, e.g. `http://localhost:11434` for local.
* **OpenRouter:** default `https://openrouter.ai/api/v1`. Override only if using a proxy or custom endpoint.

Example (Ollama local):

```yaml
provider: ollama
model:
  name: gemma3:12b
  base_url: http://localhost:11434
```

---

### `model.embedding`

**Type:** `string | null`  
**Relevant for:** `gemini`, `ollama`, `openrouter`

Model used for embeddings (RAG context search). Required when using RAG (when `review.diff_only` is `false`).

**Gemini:**, **Ollama:**, **OpenRouter:** default `BAAI/bge-small-en-v1.5` (via fastembed).

Example:

```yaml
provider: openrouter
model:
  name: openai/gpt-4o
  embedding: BAAI/bge-small-en
```

---

### Embedding and RAG Fine-Tuning

The parameters in the `model` section control the loading of the embedding model, splitting code into chunks, building the index, and the volume of context passed to the LLM. All parameters are optional.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `model.embedding` | `string` | `null` | see above | Identifier for the embedding model (fastembed). |
| `model.max_rag_chars` | `number` | `4096` | Maximum number of RAG context characters injected into the prompt. Increasing this provides more code in the context, but increases token consumption. |
| `model.max_rag_matching_chunks` | `number` | `12` | Maximum number of RAG context chunks to search in database.
| `model.max_diff_chars` | `number` | `500000` | Diff size truncation: if the diff is larger than this value, it is truncated and a truncation notice is appended at the end. |
| `model.rag_max_query_chars` | `number` | `2000` | Maximum length of the query to RAG (when searching for relevant chunks). An overly long query is truncated. |
| `model.rag_chunk_size` | `number` | `1000` | Chunk size in characters when splitting files. Code is split by function/class boundaries (tree-sitter) or by sentences. |
| `model.rag_chunk_overlap` | `number` | `200` | Overlap between adjacent chunks (in characters). Must be strictly less than `rag_chunk_size`. |
| `model.rag_embed_batch_size` | `number` | `64` | Batch size when computing embeddings. A higher value speeds up indexing if there is sufficient RAM. |
| `model.rag_threads_embedding` | `number` | `null` | `null` | Number of threads for the embedding model. `null` means auto (all CPU cores). |
| `model.rag_lazy_load` | `boolean` | `false` | Lazy loading of model weights: saves memory upon the first RAG request. |
| `model.rag_index_dir` | `string` | `.codefox/rag_index/` | Directory where the FAISS index, chunks, and metadata are stored. Changing the directory creates a separate index. |
| `model.rag_max_chunks` | `number` | `null` | Limit on the number of chunks when building the index. Useful for quick tests or limiting the index size. |
| `model.rag_max_files` | `number` | `null` | Limit on the number of files used to build the index. |
| `model.rag_min_score` | `number` | `null` | Minimum RRF score threshold during hybrid search (FAISS + BM25). Chunks with a lower score are filtered out. |

**Recommendations:**

* **For large repositories:** Decrease `rag_chunk_size` (e.g., 600-800) or set `rag_max_files` / `rag_max_chunks` to speed up indexing and reduce memory usage.
* **For more precise context:** Increase `max_rag_chars` (e.g., 6000–8000) if the model supports a long context window.
* **When memory is tight:** Enable `rag_lazy_load: true` or decrease `rag_embed_batch_size`.

Example configuration with RAG fine-tuning:

```yaml
provider: gemini
model:
  name: gemini-2.0-flash
  embedding: BAAI/bge-small-en-v1.5
  max_rag_chars: 6000
  max_diff_chars: 300000
  rag_chunk_size: 800
  rag_chunk_overlap: 150
  rag_embed_batch_size: 32
  rag_index_dir: .codefox/rag_index/
  rag_max_files: 500
review:
  diff_only: false

```

---

## 🔍 `review`

Analysis logic settings.

```yaml
review:
  severity: false
  max_issues: null
  suggest_fixes: true
  diff_only: false
```

---

### `review.severity`

**Type:** `string | false`
Filter by severity level.

Possible values:

```yaml
severity: low
severity: medium
severity: high
severity: critical
severity: false   # disable the filter
```

If set — only issues of the specified level and above are shown.

---

### `review.max_issues`

**Type:** `number | null`
Limits the number of detected issues.

Useful for:

* reducing noise
* CI mode

```yaml
max_issues: 10
```

---

### `review.suggest_fixes`

**Type:** `boolean`
**Default:** `true`

Enables generation of auto-fix patches.

If `false`:

* only comments are shown without fixes

---

### `review.diff_only`

**Type:** `boolean`
**Default:** `false`

Analysis mode:

* `true` -> only the `git diff` is analyzed
* `false` -> all files in scope are analyzed

Recommended for CI and PRs.

---

## 🧹 `baseline`

Technical debt management.

```yaml
baseline:
  enable: true
```

### `baseline.enable`

**Type:** `boolean`

If enabled:

* existing issues are ignored
* only new ones are shown

---

## 🛡 `ruler` (analysis rule set)

```yaml
ruler:
  security: true
  performance: true
  style: true
```

Enables or disables analysis categories.

---

### `ruler.security`

Searches for:

* vulnerabilities
* secret leaks
* unsafe practices

---

### `ruler.performance`

Searches for:

* inefficient algorithms
* redundant operations
* memory / query issues

---

### `ruler.style`

Checks:

* readability
* best practices
* code smells

---

## 💬 `prompt`

Model behavior customization.

```yaml
prompt:
  system: null
  extra: null
  hard_mode: false
  short_mode: false
  strict_facts: false
```

---

### `prompt.system`

**Type:** `string | null`

Completely overrides the system prompt.

Used for:

* strict internal rules
* corporate standards

Example:

```yaml
system: |
  You are a strict senior reviewer.
  Reject any unsafe code.
```

---

### `prompt.extra`

**Type:** `string | null`

Additional instructions on top of the default prompt.

Example:

```yaml
extra: |
  Follow our internal architecture guidelines.
  Ignore legacy modules.
```

---

### `prompt.hard_mode`

**Type:** `boolean`  
**Default:** `false`

Enables stricter audit rules: anti-hallucination, business logic and regression checks, concrete language and output guards, self-check. Use for high-stakes or compliance-oriented reviews.

---

### `prompt.short_mode`

**Type:** `boolean`  
**Default:** `false`

Requests shorter, more concise audit output.

---

### `prompt.strict_facts`

**Type:** `boolean`  
**Default:** `false`

Reduces hallucinations for smaller or weaker models. Enforces: use only names that appear literally in the diff, do not invent class/API/file names, do not speculate; every claim must be traceable to a line in the diff. Prefer short, direct answers and avoid filler. Recommended when using small/local models (e.g. 7B–8B).

---

# 🔌 Providers (Ollama, OpenRouter)

## Ollama

Runs analysis and RAG against a local or remote Ollama server.

* **API key:** Optional. Set `CODEFOX_API_KEY` in `.codefoxenv` if your Ollama instance requires auth.
* **Models:** Use `codefox --command list` to see models available on your server.
* **Default model:** `gemma3:12b`
* **RAG:** Uploaded files are chunked and embedded using `model.embedding` (default `BAAI/bge-small-en-v1.5`). Ensure the embedding model is pulled in Ollama.

Minimal `.codefox.yml`:

```yaml
provider: ollama
model:
  name: gemma3:12b
  base_url: http://localhost:11434   # optional, default https://ollama.com
  embedding: BAAI/bge-small-en-v1.5  # optional, for RAG
review:
  diff_only: true
```

---

## OpenRouter

Uses OpenRouter to run many third-party models (OpenAI, Anthropic, Qwen, etc.) with a single API key.

* **API key:** Required. Set `CODEFOX_API_KEY` in `.codefoxenv` to your OpenRouter API key.
* **Models:** Use `codefox --command list` to see available models.
* **Default model:** `qwen/qwen3-vl-30b-a3b-thinking`
* **RAG:** Embeddings use `model.embedding` (default `text-embedding-3-small`). File upload and context search are supported.

Minimal `.codefox.yml`:

```yaml
provider: openrouter
model:
  name: openai/gpt-4o
  embedding: text-embedding-3-small  # optional
  max_completion_tokens: 4096       # optional
review:
  diff_only: true
```

---

# 🧩 Full configuration example

**Gemini:**

```yaml
provider: gemini
model:
  name: gemini-3-pro
  temperature: 0.1
  max_tokens: 4000
  timeout: 600

review:
  severity: high
  max_issues: 15
  suggest_fixes: true
  diff_only: true

baseline:
  enable: true

ruler:
  security: true
  performance: false
  style: false

prompt:
  hard_mode: false
  short_mode: false
  extra: |
    Use our NestJS architecture rules.
```

**Ollama (local):**

```yaml
provider: ollama
model:
  name: gemma3:12b
  base_url: http://localhost:11434
  embedding: BAAI/bge-small-en-v1.5
  temperature: 0.2
  max_tokens: 4000
  timeout: 600
review:
  diff_only: true
  severity: high
```

**OpenRouter:**

```yaml
provider: openrouter
model:
  name: openai/gpt-4o
  embedding: text-embedding-3-small
  temperature: 0.2
  max_tokens: 4000
  max_completion_tokens: 4096
  timeout: 600
review:
  diff_only: true
  severity: high
```

---

## 🧪 Recommended profiles

### CI mode

```yaml
review:
  diff_only: true
  severity: high
  max_issues: 10
```

### Legacy project

```yaml
baseline:
  enable: true
review:
  diff_only: true
```
