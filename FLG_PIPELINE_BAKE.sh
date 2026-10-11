#!/bin/bash
set -e
cd ~/FLG-OS
echo "*** FLG PIPELINE BAKE START ***"

# 1. Phone Storage (.md Specs)
mkdir -p docs/specs docs/brain docs/themes
cat << 'SPEC_EOF' > docs/specs/FLG_SYSTEM_SPEC.md
# FLG System Spec - Markdown-Driven Source of Truth
# Core DNA: Phase 2 Real Pipeline
- Reactor: local_broker.py @ 127.0.0.1:8000/stats
SPEC_EOF

# 2. Mintlify Configuration
cat << 'MINT_EOF' > mint.json
{
  "$schema": "https://mintlify.com/schema.json",
  "name": "FLG Engine Docs",
  "logo": "/logo.png",
  "favicon": "/favicon.png",
  "colors": {
    "primary": "#00F0FF",
    "light": "#00F0FF",
    "dark": "#FF0033"
  },
  "navigation": [
    {
      "group": "System Specs",
      "pages": ["docs/specs/FLG_SYSTEM_SPEC"]
    }
  ]
}
MINT_EOF

mkdir -p docs
cat << 'INTRO_EOF' > docs/intro.mdx
---
title: "FLG OS System Blueprint"
description: "Self-bootstrapping autonomous AI software factory"
---
# Welcome to FLG Engine
INTRO_EOF

# 3. GitHub Agentic Workflows (gh-aw)
mkdir -p .github/workflows
cat << 'GHAW_EOF' > .github/workflows/gh-aw-flg-compile.yml
name: FLG Agentic Spec Compiler
on:
  push:
    paths:
      - 'docs/specs/**'
jobs:
  compile-spec:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Spec Engine
        run: echo "Compiling FLG Specs into Code Pipeline..."
GHAW_EOF

# 4. CodeRabbit Configuration
cat << 'CR_EOF' > .coderabbit.yaml
language: "en-US"
reviews:
  profile: "chill"
  request_changes_workflow: false
  high_level_summary: true
  poem: false
CR_EOF

# 5. MCP Local Broker Config
mkdir -p .vscode
cat << 'MCP_EOF' > .vscode/mcp.json
{
  "mcpServers": {
    "flg-broker": {
      "command": "python3",
      "args": ["local_broker.py"]
    }
  }
}
MCP_EOF

echo "*** FLG PIPELINE BAKE COMPLETE ***"
