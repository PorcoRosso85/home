<div align="center"><sub>
<a href="./tools/cc-sdd/README.md">English</a> | <a href="./tools/cc-sdd/README_ja.md">日本語</a> | <a href="./tools/cc-sdd/README_zh-TW.md">繁體中文</a>
</sub></div>

# cc-sdd / Claude Code Spec


> 📦 **Beta Release** - Ready to use, actively improving. [Report issues →](https://github.com/gotalab/claude-code-spec/issues)

  <!-- npm badges -->
  [![npm version](https://img.shields.io/npm/v/cc-sdd?logo=npm)](https://www.npmjs.com/package/cc-sdd?activeTab=readme)
  [![license: MIT](https://img.shields.io/badge/license-MIT-green.svg)](tools/cc-sdd/LICENSE)


One command installs **AI-DLC** (AI-Driven Development Life Cycle) with **SDD** (Spec-Driven Development) workflows for Claude Code and Gemini CLI.

## 🚀 Quick Start

```bash
# Basic installation (default: Claude Code)
npx cc-sdd@latest

# With language: --lang en (English) or --lang ja (Japanese) or --lang zh-TW (Traditional Chinese)
# With OS: --os mac | --os windows | --os linux (if auto-detection fails)
npx cc-sdd@latest --lang ja --os mac

# With different agents: gemini-cli
npx cc-sdd@latest --gemini-cli

# Ready to go! Now Claude Code and Gemini CLI can leverage `/kiro:spec-init <what to build>` and the full SDD workflow
```

## ✨ What You Get

After running cc-sdd, you'll have:

- **8 powerful slash commands** (`/kiro:steering`, `/kiro:spec-requirements`, etc.)
- **Project Memory (steering)** - AI learns your codebase, patterns, and preferences
- **Structured AI-DLC workflow** with quality gates and approvals
- **Spec-Driven Development** methodology built-in
- **Kiro IDE compatibility** for seamless spec management

**Perfect for**: Feature development, code reviews, technical planning, and maintaining development standards across your team.

---

## About

Includes Claude Code your project context, Project Memory (steering) and development patterns: **requirements → design → tasks → implementation**. **Kiro IDE compatible** — Reuse Kiro-style SDD specs and workflows seamlessly.

【Claude Code/Gemini CLI】ワンライナーで **AI-DLC（AI-Driven Development Life Cycle）** と **Spec-Driven Development（仕様駆動開発）** のワークフローを導入。プロジェクト直下に **Slash Commands** 一式と設定ファイル（Claude Code用の **CLAUDE.md** / Gemini CLI用の **GEMINI.md**）を配置し、プロジェクトの文脈と開発パターン（**要件 → 設計 → タスク → 実装**）、**プロジェクトメモリ（ステアリング）** を含みます。

📝 **関連記事**  
**[Kiroの仕様書駆動開発プロセスをClaude Codeで徹底的に再現した](https://zenn.dev/gotalab/articles/3db0621ce3d6d2)** - Zenn記事

## Languages
> 📖 **Project Overview** (Spec-Driven Development workflow)
> • 日本語: [README_ja.md](README_ja.md)
> • English: [README_en.md](README_en.md)
> • 繁體中文: [README_zh-TW.md](README_zh-TW.md)

**Transform your agentic development workflow with Spec-Driven Development**

---

## 🤖 Supported Coding Agents

- **✅ Claude Code** - Fully supported with all 8 custom slash commands and CLAUDE.md
- **✅ Gemini CLI** - Fully supported with all 8 custom commands and GEMINI.md
- **📅 More agents** - Additional AI coding assistants planned

*Currently optimized for Claude Code. Use `--agent claude-code` (default) for full functionality.*
 
## 📋 AI-DLC Workflow

**Step 0: Setup Project Memory (Recommended)**
```bash
# Teach Claude Code about your project
/kiro:steering
```

**SDD Development Flow:**
```bash
# 1. Start a new feature spec
/kiro:spec-init User authentication with OAuth and 2FA

# 2. Generate detailed requirements  
/kiro:spec-requirements user-auth

# 3. Create technical design (after requirements review)
/kiro:spec-design user-auth -y

# 4. Break down into tasks (after design review)  
/kiro:spec-tasks user-auth -y

# 5. Implement with TDD (after task review)
/kiro:spec-impl user-auth 1.1,1.2,1.3
```

**Quality Gates**: Each phase requires human approval before proceeding (use `-y` to auto-approve).

## 🎯 Advanced Options

```bash
# Choose language and OS
npx cc-sdd@latest --lang ja --os mac

# Preview changes before applying
npx cc-sdd@latest --dry-run

# Safe update with backup
npx cc-sdd@latest --backup --overwrite force

# Custom specs directory
npx cc-sdd@latest --kiro-dir docs/specs
```

## Features

✅ **AI-DLC Integration** - Complete AI-Driven Development Life Cycle  
✅ **Project Memory** - Steering that learns your codebase and patterns  
✅ **Spec-Driven Development** - Structured requirements → design → tasks → implementation  
✅ **Cross-Platform** - macOS, Linux, and Windows support with auto-detection (Linux reuses mac templates)  
✅ **Multi-Language** - Japanese, English, Traditional Chinese  
✅ **Safe Updates** - Interactive prompts with backup options  

## 📚 Related Resources

📝 **Related Articles**  
**[Kiroの仕様書駆動開発プロセスをClaude Codeで徹底的に再現した](https://zenn.dev/gotalab/articles/3db0621ce3d6d2)** - Zenn Article (Japanese)

## 📦 Package Information

This repository contains the **cc-sdd** NPM package located in [`tools/cc-sdd/`](tools/cc-sdd/).

For detailed documentation, installation instructions, and usage examples, see:
- [**Tool Documentation**](tools/cc-sdd/README.md) - Complete cc-sdd tool guide
- [**Japanese Documentation**](tools/cc-sdd/README_ja.md) - 日本語版ツール説明

## Project Structure

```
claude-code-spec/
├── tools/cc-sdd/              # Main cc-sdd NPM package
│   ├── src/                   # TypeScript source code
│   ├── templates/             # Agent templates (Claude Code, Gemini CLI)
│   ├── package.json           # Package configuration
│   └── README.md              # Tool documentation
├── docs/                      # Documentation
├── .claude/                   # Example Claude Code commands
├── .gemini/                   # Example Gemini CLI commands
├── README.md                  # This file (English)
├── README_ja.md               # Japanese project README
└── README_zh-TW.md            # Traditional Chinese project README
```


## License

MIT License
