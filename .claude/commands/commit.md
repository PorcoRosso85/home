# /commit - Git commit only Claude-edited files

## Purpose
Commit only the files that you (Claude) have edited in the current session, excluding any files modified by others.

## Usage
When the user says "commit", "/commit", or mentions "git commit":

1. First run `git status` to see all changed files
2. Identify which files you have edited during this conversation
3. Stage ONLY those files you edited
4. Create a commit with a descriptive message
5. Ensure no other files are accidentally included

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
```

## Key Principle
"Commit only your files except for others" - This ensures clean commit history and prevents accidental inclusion of work done by other developers or tools.