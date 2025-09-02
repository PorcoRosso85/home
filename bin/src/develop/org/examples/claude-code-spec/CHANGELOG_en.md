# Update Information

Updates for Claude Code Spec-Driven Development.

---

## Ver 0.3.0 (August 12, 2025 Update)

### Major Kiro Spec-Driven Development Command Improvements

**Workflow Efficiency**
- Added `-y` flag: `/kiro:spec-design feature-name -y` skips requirements approval and generates design
- `/kiro:spec-tasks feature-name -y` skips requirements+design approval and generates tasks  
- Added argument-hint: Commands now auto-display `<feature-name> [-y]` during input
- Traditional step-by-step approval still available (spec.json editing or interactive approval)

**Command Optimization**
- spec-init.md: 162→104 lines (36% reduction, removed project_description and simplified templates)
- spec-requirements.md: 177→124 lines (30% reduction, simplified verbose explanations)
- spec-tasks.md: 295→198 lines (33% reduction, eliminated "Phase X:", functional naming, granularity optimization)

**Task Structure Optimization**
- Section headers for functional area organization
- Task granularity limits (3-5 sub-items, 1-2 hour completion)
- Standardized _Requirements: X.X, Y.Y_ format

**Custom Steering Support**
- All spec commands now utilize project-specific context
- Flexible Always/Conditional/Manual mode configuration loading

---

## Ver 0.2.1 (July 27, 2025 Update)

### CLAUDE.md Performance Optimization

**System Prompt Optimization**
- Reduced CLAUDE.md files from 150 lines to 66 lines
- Removed duplicate sections and redundant explanations
- Implemented unified optimization across Japanese, English, and Traditional Chinese versions

**Functionality Preservation**
- Maintained all essential execution context
- Preserved steering configuration and workflow information
- No impact on interactive approval functionality

**Minor Updates**
- Added "think" keyword to spec-requirements.md

---

## Ver 0.2.0 (July 26, 2025 Update)

### Interactive Approval System

**Approval Flow Improvements**
- `/spec-design [feature-name]` now displays "Have you reviewed requirements.md? [y/N]" confirmation prompt
- `/spec-tasks [feature-name]` now displays review confirmation for both requirements and design
- 'y' approval automatically updates spec.json and proceeds to next phase
- 'N' selection stops execution and prompts for review

**Simplified Operations**
- Previous: Manual editing of spec.json file required to set `"approved": true`
- Current: Simple response to confirmation prompt completes approval
- Manual approval method remains available

### Specification Generation Quality Improvements

**Enhanced requirements.md Generation**
- EARS format output now generates in more unified format
- Hierarchical requirement structure outputs in more organized format
- Improved comprehensiveness and specificity of acceptance criteria

**Enhanced design.md**
- Technical research process now integrated into design phase
- Requirements mapping and traceability reflected in design documents
- Improved document structure for architecture diagrams, data flow diagrams, ERDs
- More detailed descriptions of security, performance, and testing strategies

**Improved tasks.md**
- Implementation tasks optimized for code generation LLMs
- Test-driven development approach integrated into each task
- Clearer management of inter-task dependencies
- Improved to independent prompt format aligned with Kiro design principles

### Fixed Issues

**Improved Directory Handling**
- Now works properly even when `.kiro/steering/` directory doesn't exist
- More user-friendly error messages

**Improved Internal File Management**
- Excluded development prompt files from version control

### System Design Simplification

**Removed progress Field**
- Completely removed redundant progress field that caused sync errors
- Achieved clearer state management with only phase + approvals
- Simplified spec.json structure and improved maintainability

**Revised Requirements Generation Approach**
- Reverted from overly comprehensive requirements generation to original Kiro design
- Removed forceful expressions like "CRITICAL" and "MUST"
- Changed to gradual requirements generation focused on core functionality
- Restored natural development flow premised on iterative improvement

---

## Ver 0.1.5 (July 25, 2025 Update)

### Major Steering System Enhancement

**Enhanced Security Features**
- Added security guidelines and content quality guidelines
- Enabled safer and higher quality project management

**Improved inclusion modes Functionality**
- Three modes (Always included, Conditional, Manual) are now more user-friendly
- Added detailed usage recommendations and guidance

**Unified Steering Management Functions**
- `/kiro:steering` command now properly handles existing files
- More intuitive steering document management

**Improved System Stability**
- Fixed Claude Code pipe bugs for more reliable execution
- Now works properly in non-Git environments

---

## Ver 0.1.0 (July 18, 2025 Update)

### Basic Features
- Implemented Kiro IDE-style specification-driven development system
- 3-phase approval workflow: Requirements → Design → Tasks → Implementation
- EARS format requirements definition support
- Hierarchical requirements structure organization
- Automatic progress tracking and hook functionality
- Basic Slash Commands set

### Quality Management Features
- Quality assurance through manual approval gates
- Specification compliance check functionality
- Context preservation functionality

---

## Ver 0.0.1 (July 17, 2025 Update)

### New Features
- Created initial project structure

---

## Development History

**July 17-18, 2025: Foundation Building Period**
Project initialization and implementation of core framework for Kiro-style specification-driven development

**July 18-24, 2025: Multilingual & Feature Expansion Period**
Added English and Traditional Chinese support, GitHub Actions integration, enhanced documentation

**July 25, 2025: Steering System Enhancement Period**
Security enhancements, inclusion modes improvements, system stability improvements

**July 26, 2025: Specification Generation Quality Innovation & System Simplification**
Significantly improved generation quality of requirements, design, and tasks documents, removed excessive progress tracking and returned to original Kiro design

---

## Usage

1. Copy **`.claude/commands/` directory** and **`CLAUDE.md` file** to your project
2. Run `/kiro:steering` in Claude Code to configure project information
3. Create new specifications with `/kiro:spec-init [feature-name]`
4. Progress through development step by step: requirements → design → tasks

For detailed usage instructions, see [README_en.md](README_en.md).

## Related Links

- **[Zenn Article](https://zenn.dev/gotalab/articles/3db0621ce3d6d2)** - Detailed explanation of Kiro's specification-driven development process
- **[Japanese Documentation](README.md)**
- **[Traditional Chinese Documentation](README_zh-TW.md)**