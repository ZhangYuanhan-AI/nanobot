# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_some_file.py -v

# Lint
ruff check nanobot/

# Format
ruff format nanobot/
```

## Code Style

- Python 3.11+, line length 100 chars
- Ruff rules: E, F, I, N, W (E501 ignored)
- Async throughout (`asyncio`); tests use `asyncio_mode = "auto"` via pytest-asyncio
- Prefer focused patches over broad rewrites; new abstractions should clearly reduce complexity

## Architecture

**nanobot** is an ultra-lightweight personal AI assistant framework (~5,000 core agent lines). The entry point is the `nanobot` CLI (typer) defined in `nanobot/cli/commands.py`.

### Core Agent (`nanobot/agent/`)
- **loop.py** — `AgentLoop`: main processing engine. Receives messages from the bus, builds context (system prompt + memory + skills + history), calls the LLM with tool definitions, executes tool calls, and publishes responses. Max 40 iterations per turn, token-aware context management (65,536 token window).
- **context.py** — Context building: assembles system prompt, memory, skills, and conversation history for LLM calls.
- **memory.py** — Two-layer memory: `MEMORY.md` (long-term facts) and `HISTORY.md` (timestamped grep-searchable log). Consolidation summarizes old conversations to stay within the context window.
- **subagent.py** — Sub-agent spawning with isolated workspace copies.
- **skills.py** — Loads skills from `SKILL.md` files (YAML frontmatter + markdown instructions).
- **tools/** — Tool registry pattern. Each tool extends a `Tool` base class with `name`, `description`, `parameters`, `execute()`. Built-in tools: filesystem (read/write/edit/listdir), shell exec, web search/fetch, message, spawn, cron, MCP integration.

### Message Bus (`nanobot/bus/`)
Simple async queue decoupling channels from the agent loop. `InboundMessage` (channel→agent) and `OutboundMessage` (agent→channel).

### Channels (`nanobot/channels/`)
Chat platform integrations (Telegram, Discord, Slack, Feishu, DingTalk, Matrix, QQ, WeChat Work, WhatsApp, Email, etc.). All extend `BaseChannel` ABC with `start()`, `stop()`, `send()`. Managed by `ChannelManager`.

### Providers (`nanobot/providers/`)
LLM provider adapters behind `LLMProvider` ABC. `LiteLLMProvider` handles most models; specialized adapters for Azure OpenAI, custom OpenAI-compatible endpoints, and Codex OAuth. Auto-detection by model prefix (e.g., `anthropic/claude-opus-4-5`).

### Config (`nanobot/config/`)
Pydantic-based config schema (`schema.py`). Loaded from `~/.nanobot/config.json`. Supports CamelCase/snake_case interop, extra fields in channel configs for plugins.

### Session (`nanobot/session/`)
Conversation history stored as JSONL per channel+chat_id. Append-only for LLM cache efficiency. Legal boundary preservation (no orphaned tool calls).

### Other Services
- **cron/** — CronService for scheduled jobs.
- **heartbeat/** — Keep-alive pings for gateway deployments.
- **security/** — URL validation and network security checks.
- **bridge/** — Node.js/TypeScript WhatsApp bridge (Baileys-based, Socket.IO).

### Skills (`nanobot/skills/`)
Extensible capabilities loaded from `SKILL.md` files: github, weather, summarize, tmux, clawhub, memory, cron, skill-creator.

### Templates (`nanobot/templates/`)
Bootstrap templates synced to workspace on startup: AGENTS.md, SOUL.md, USER.md, TOOLS.md, memory templates.

## Branching Strategy

- **`main`** — Stable releases. Target for bug fixes, docs, minor tweaks.
- **`nightly`** — Experimental features. Target for new features, refactoring, API changes.
- When in doubt, target `nightly`. Stable features are cherry-picked from nightly→main weekly.
