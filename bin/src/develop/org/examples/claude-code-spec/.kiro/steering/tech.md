# Technology Stack

## Architecture

Documentation-driven framework built on Claude Code's native extensibility features. The architecture consists of three main layers:

1. **Command Layer**: Markdown-based slash commands with dynamic content generation
2. **Automation Layer**: Python-based hooks for automated progress tracking and validation
3. **Knowledge Layer**: Structured markdown documents for persistent project context

## Core Technologies

### Claude Code Platform
- **Base Platform**: Claude Code CLI (Anthropic's official Claude interface)
- **Model**: Claude Sonnet 4 (claude-sonnet-4-20250514)
- **Extension System**: Native hooks and slash commands support
- **Context Management**: Built-in compaction with preservation hooks

### Command System
- **Definition Format**: Markdown files with YAML frontmatter
- **Dynamic Content**: Bash execution (`!command`) and file inclusion (`@file.md`)
- **Argument Passing**: `$ARGUMENTS` variable for parameter handling
- **Tool Restrictions**: `allowed-tools` specification for security

### Hook System
- **Configuration**: JSON-based hook definitions in `.claude/settings.json`
- **Execution Environment**: Python 3 scripts with JSON I/O
- **Event Types**: PostToolUse, PreToolUse, PreCompact, Stop
- **Performance**: Configurable timeouts (5-10 seconds typical)

## Development Environment

### Required Tools
- **Claude Code**: Latest version with hooks and slash commands support
- **Python 3**: For hook scripts (progress tracking, validation)
- **Git**: For version control and change detection
- **Markdown Editor**: For document editing and review

### Project Structure
```
.claude/
├── commands/kiro/           # Slash command definitions
│   ├── steering*.md         # Steering management commands
│   ├── spec-*.md           # Specification workflow commands
│   └── *.md                # Additional command definitions
├── scripts/                 # Hook automation scripts
│   ├── check-steering-drift.py
│   ├── update-spec-progress.py
│   └── preserve-spec-context.py
└── settings.json           # Hook configuration

.kiro/
├── steering/               # Project knowledge documents
│   ├── product.md
│   ├── tech.md
│   └── structure.md
└── specs/                  # Feature specifications
    └── [feature-name]/
        ├── spec.json       # Metadata and approval flags
        ├── requirements.md
        ├── design.md
        └── tasks.md
```

## Common Commands

### Core Workflow Commands
```bash
# Steering management (recommended unified command)
/kiro:steering                    # Smart create/update steering documents

# Specification workflow
/kiro:spec-init [description]     # Initialize new specification
/kiro:spec-requirements [name]    # Generate requirements document
/kiro:spec-design [name]          # Generate technical design
/kiro:spec-tasks [name]           # Generate implementation tasks
/kiro:spec-status [name]          # Check progress and compliance
```

### Legacy Commands (Deprecated)
```bash
# These commands are maintained for compatibility but not recommended
/kiro:steering-init              # [DEPRECATED] Use /kiro:steering instead
/kiro:steering-update            # [DEPRECATED] Use /kiro:steering instead
/kiro:steering-custom            # Still used for specialized steering documents
```

### Manual Operations
```bash
# Project setup (one-time)
cp -r .claude/ /your-project/     # Copy command definitions
cp CLAUDE.md /your-project/       # Copy project configuration

# Progress management
# Edit spec.json manually to approve phases:
# "requirements": true, "design": true, "tasks": true
```

## Environment Variables

### Claude Code Configuration
- **CLAUDE_HOOKS_ENABLED**: Enable hook system (default: true)
- **CLAUDE_COMMAND_TIMEOUT**: Command execution timeout (default: 120s)
- **CLAUDE_CONTEXT_PRESERVATION**: Enable context hooks (default: true)

### Project Configuration
- **KIRO_LANGUAGE**: Default language for generated content (ja/en/zh-TW)
- **KIRO_STEERING_MODE**: Steering inclusion mode (always/conditional/manual)
- **KIRO_SPEC_VALIDATION**: Enable specification validation (default: true)

## Hook Configuration Details

### PostToolUse Hooks
```json
{
  "matcher": "Edit|MultiEdit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "python3 .claude/scripts/check-steering-drift.py",
      "timeout": 10
    }
  ]
}
```

### PreCompact Hooks  
```json
{
  "matcher": ".*",
  "hooks": [
    {
      "type": "command", 
      "command": "python3 .claude/scripts/preserve-spec-context.py",
      "timeout": 5
    }
  ]
}
```

## Performance Characteristics

- **Command Execution**: 2-5 seconds for simple commands, 10-30 seconds for document generation
- **Hook Overhead**: 1-3 seconds per file operation when hooks are active
- **Context Preservation**: 95%+ success rate in maintaining spec context during compaction
- **Steering Accuracy**: Automated drift detection with ~90% precision for significant changes

## Integration Points

### Git Integration
- Hook scripts detect file changes using git status
- Commit messages can reference specification phases
- Steering drift detection based on git diff analysis

### Documentation Systems
- Compatible with standard markdown documentation workflows
- Generates content suitable for wikis, README files, and technical documentation
- Supports multi-language documentation maintenance

### CI/CD Compatibility
- Hook scripts can be adapted for continuous integration
- Specification compliance can be validated in automated pipelines
- Progress tracking suitable for project management tool integration