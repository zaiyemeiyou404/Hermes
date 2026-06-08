---
name: code-intelligence-tools
description: Install and configure code intelligence and knowledge-graph tools that help AI coding agents understand codebases faster — CodeGraph, tree-sitter, and similar indexing tools.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [codegraph, indexing, code-intelligence, knowledge-graph, agent-sd]
    related_skills: [opencode, claude-code, codex, hermes-agent]
---

# Code Intelligence Tools

## Overview

Code intelligence tools build structured indexes (knowledge graphs, AST maps, call graphs) of a codebase so AI coding agents don't need to re-scan all files on every query. This reduces token consumption by ~59% and speeds up responses by ~49% on typical projects.

**Supported agents** (auto-detected by CodeGraph): Claude Code, Codex CLI, OpenCode, Hermes Agent, Cursor, Gemini CLI, Qwen Code, GitHub Copilot CLI, and others.

## CodeGraph — Installation

### Interactive (recommended for first-time setup)

```bash
npx @colbymchenry/codegraph
```

This scans the user's PATH for installed coding agents and prompts which to configure. Detected agents are pre-selected with ◼; press Enter to confirm.

### Non-interactive (for automation / remote sessions)

```bash
npx @colbymchenry/codegraph install --yes
```

Defaults to `--location=global --target=auto`, configuring all detected agents automatically. This **installs CodeGraph as an MCP server** into each agent, creating/modifying:

| Agent | Config files created/updated |
|-------|---------------------------|
| Claude Code | `~/.claude.json`, `~/.claude/settings.json`, `~/.claude/CLAUDE.md` |
| Codex CLI | `~/.codex/config.toml`, `~/.codex/AGENTS.md` |
| OpenCode | `~/.config/opencode/opencode.jsonc`, `~/.config/opencode/AGENTS.md` |
| Hermes Agent | `~/.hermes/config.yaml` |

Restart the agents after installation for MCP changes to take effect. See `codegraph install --help` for more flags.

## CodeGraph — Project Initialization

After installation, enter each project and build its knowledge graph:

```bash
cd /path/to/project
codegraph init -i
```

This scans all source files, parses them into nodes (functions, classes, imports, types, etc.) and edges (call relationships), and stores the graph in a local SQLite database at `.codegraph/`.

### Verification

```bash
# Show index stats
codegraph status

# Query for symbols
codegraph query "FunctionName"
```

Example output for a 30-file project:
```
Files:     30
Nodes:     392
Edges:     839
DB Size:   1.07 MB
```

### Query syntax

`codegraph query <search-term>` searches indexed symbols by name, showing:

```
function    FunctionName (relevance%)
  src/components/file.tsx:line
  ({ params })

import      @/path (relevance%)
  src/other-file.ts:line
  import { FunctionName } from "@/path"
```

Relevance scores help distinguish primary definitions from references.

## CodeGraph — macOS Prerequisites

On macOS, Xcode command-line tools must be installed **before** running `codegraph init`. Without them, CodeGraph falls back to a compatibility mode that is 5-10× slower:

```bash
xcode-select --install
```

## CodeGraph — Pitfalls

| Pitfall | Solution |
|---------|----------|
| Interactive prompt hangs in headless sessions | Use `--yes` flag for non-interactive install |
| macOS slow indexing | Install Xcode CLI tools first |
| Query returns no results | Search by function/class/symbol names, not arbitrary text |
| Lock file prevents re-indexing | `codegraph unlock` clears stale lock files |
| Pre-1.0 version instability | Check for updates regularly: `npx @colbymchenry/codegraph` |

## When to Use

- **Install** once per machine (configures all coding agents globally)
- **Initialize** once per project (builds the knowledge graph)
- **Re-index** when large structural changes occur (new modules, refactors)
- **Query** for rapid codebase exploration without file-grepping
