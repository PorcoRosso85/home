※必ず末尾まで100%理解したと断言できる状態になってから指示に従うこと
※このコマンドの説明はそれほど重要であるということを理解すること

# /commit - Git commit only Claude-edited files

## Purpose
Commit only the files that you (Claude) have edited in the current session, excluding any files modified by others.

## Usage
When the user says "commit", "/commit", or mentions "git commit":

0. 禁止事項確認: `bin/docs/conventions/prohibited_items.md`
1. First run `git status` to see all changed files
2. Identify which files you have edited during this conversation
3. Stage ONLY those files you edited
4. Create a commit with a descriptive message
5. Ensure no other files are accidentally included
6. After commit, check for remaining uncommitted files in current directory (pwd) only
7. If uncommitted files exist in pwd, explain why they weren't included

## Important Rules
- NEVER commit files you didn't edit
- Always verify staged files before committing
- Use the commit message format from bin/docs/conventions/commit_messages.md
- Include the Claude signature in commit messages

## Example Flow
```bash
# 1. Check status
git status

# 2. Reset all staged files
git reset HEAD

# 3. Add only your edited files
git add path/to/your-file1.txt
git add path/to/your-file2.py

# 4. Verify staged files
git status

# 5. Commit with proper message
git commit -m "feat: implement new feature

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 6. Check for remaining changes in current directory only
git status .

# 7. If uncommitted files exist, explain each:
# - .claude/projects/*.jsonl → Session tracking files (not my edits)
# - bin/src/other/file.py → Modified by another developer/tool
# - test_output.log → Generated file (not source code)
```

## Post-Commit Analysis
After committing, analyze remaining uncommitted files in the current directory (pwd) only:

### Check scope:
- Use `git status .` to check only files in current directory and subdirectories
- Ignore files outside of pwd to focus on relevant changes
- This prevents unnecessary analysis of unrelated project files

### Common reasons for uncommitted files:
1. **Session tracking files** (`.claude/projects/*.jsonl`) - Automatic session logs
2. **Other developer's work** - Files modified by team members or other tools
3. **Generated files** - Build outputs, logs, temporary files
4. **Unrelated changes** - Files outside current task scope
5. **Incomplete work** - Files requiring further modifications

### Working directory focus:
- Only analyze files within pwd and its subdirectories
- Example: If pwd is `/home/nixos/bin/src/poc/`, only check that path
- Skip global repository status to maintain focused analysis

## Key Principle
"Commit only your files except for others" - This ensures clean commit history and prevents accidental inclusion of work done by other developers or tools.