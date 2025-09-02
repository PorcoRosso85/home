# cc-sdd

✨ **Transform Claude Code/Gemini CLI from prototype to production-ready development**

<!-- npm badges -->
[![npm version](https://img.shields.io/npm/v/cc-sdd?logo=npm)](https://www.npmjs.com/package/cc-sdd?activeTab=readme)
[![npm downloads](https://img.shields.io/npm/dm/cc-sdd?logo=npm)](https://www.npmjs.com/package/cc-sdd)
[![install size](https://packagephobia.com/badge?p=cc-sdd)](https://packagephobia.com/result?p=cc-sdd)
[![license: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

<div align="center"><sub>
English | <a href="https://github.com/gotalab/claude-code-spec/blob/main/tools/cc-sdd/README_ja.md">日本語</a> | <a href="https://github.com/gotalab/claude-code-spec/blob/main/tools/cc-sdd/README_zh-TW.md">繁體中文</a>
</sub></div>

Brings **AI-DLC (AI Driven Development Lifecycle)** to Claude Code and Gemini CLI. **AI-native processes** with **minimal human approval gates**: AI drives execution while humans validate critical decisions at each phase.

🎯 **Perfect for**: Escaping the 70% overhead trap of traditional development (meetings, documentation, ceremonies) to achieve **weeks-to-hours delivery** with AI-native execution and human quality gates.

> **Kiro compatible** — Same proven workflow used in professional environments.

## 🚀 Installation

```bash
# Basic installation (defaults: English docs, Claude Code agent)
npx cc-sdd@latest

# With language options (default: --lang en)
npx cc-sdd@latest --lang ja    # Japanese
npx cc-sdd@latest --lang zh-TW # Traditional Chinese

# With agent options (default: claude-code)
npx cc-sdd@latest --gemini-cli --lang ja # For Gemini CLI instead
```

## ✨ Quick Demo

```bash
# Launch AI agent: 'claude' or 'gemini'

# AI-DLC Core Pattern in Action:
/kiro:spec-init Build a user authentication system with OAuth  # AI creates plan
/kiro:spec-requirements auth-system                            # AI asks clarifying questions  
/kiro:spec-design auth-system                                  # Human validates, AI implements
/kiro:spec-tasks auth-system                                   # Repeat: Plan → Ask → Validate → Implement
```

**30-second setup** → **AI-driven "bolts" (not sprints)** → **Hours-to-delivery results**

## ✨ Key Features

- **🚀 AI-DLC Methodology** - AI-native processes with human approval. Core pattern: AI executes, human validates
- **📋 Spec-First Development** - Comprehensive specifications as single source of truth driving entire lifecycle
- **⚡ "Bolts" not Sprints** - Hours/days cycles instead of weeks. Escape the 70% administrative overhead
- **🧠 Project Memory** - AI maintains persistent context across sessions, learns your patterns  
- **🔄 AI-Native + Human Gates** - AI Plans → AI Asks → Human Validates → AI Implements (rapid cycles with quality control)
- **🌍 Team-Ready** - Multi-language, cross-platform, standardized workflows with quality gates

## 🤖 Supported AI Agents

| Agent | Status | Commands | Config |
|-------|--------|----------|--------|
| **Claude Code** | ✅ Full | 8 slash commands | `CLAUDE.md` |
| **Gemini CLI** | ✅ Full | 8 commands | `GEMINI.md` |
| Others | 📅 Planned | - | - |
 
## 📋 Core Commands

### Development Workflow
```bash
/kiro:spec-init <description>             # Initialize feature spec
/kiro:spec-requirements <feature_name>    # Generate requirements
/kiro:spec-design <feature_name>          # Create technical design  
/kiro:spec-tasks <feature_name>           # Break into implementation tasks
/kiro:spec-impl <feature_name> <tasks>    # Execute with TDD
/kiro:spec-status <feature_name>          # Check progress
```

### Project Setup
```bash
/kiro:steering                            # Create/update project memory
/kiro:steering-custom                     # Custom guidance rules
```

## ⚙️ Configuration

```bash
# Language and platform
npx cc-sdd@latest --lang ja --os mac   # macOS
npx cc-sdd@latest --lang ja --os linux # Linux (shares mac templates)

# Safe operations  
npx cc-sdd@latest --dry-run --backup

# Custom directory
npx cc-sdd@latest --kiro-dir docs/specs
```

## 📁 Project Structure

After installation, your project gets:

```
project/
├── .claude/commands/kiro/    # 8 slash commands
├── .kiro/specs/             # Feature specifications
├── .kiro/steering/          # AI guidance rules
└── CLAUDE.md                # Project configuration
```

## 📚 Documentation & Support

- **[Full Documentation](https://github.com/gotalab/claude-code-spec/blob/main/README.md)** - Complete setup guide
- **[Command Reference](https://github.com/gotalab/claude-code-spec/docs)** - All options and examples  
- **[Issues & Support](https://github.com/gotalab/claude-code-spec/issues)** - Bug reports and questions
- **[Kiro IDE Integration](https://kiro.dev)** - Enhanced spec management

---

**Beta Release** - Ready to use, actively improving. [Report issues](https://github.com/gotalab/claude-code-spec/issues) | MIT License

### Platform Support
- Supported OS: macOS, Linux, Windows (auto-detected by default).
- Linux uses the same command templates as macOS. Windows has dedicated templates.
