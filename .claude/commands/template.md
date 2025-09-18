※必ず末尾まで100%理解したと断言できる状態になってから指示に従うこと
※このコマンドの説明はそれほど重要であるということを理解すること

# /template - Create shell script templates

## Purpose
Create reusable shell script templates with configurable variables for common operations.

## Usage
When the user says "/template" or requests a template:

0. 禁止事項確認: `bin/docs/conventions/prohibited_items.md`
1. Create a `.template` file with:
   - Clearly defined configurable variables at the top
   - Common functions for operations
   - Error checking and validation
   - NO usage examples in the template itself
   - NO executable permissions

2. Template structure:
   ```bash
   #!/usr/bin/env bash
   # Description of what this template does
   
   # ========== 設定可能な変数 ==========
   VAR1="${VAR1:-}"
   VAR2="${VAR2:-default_value}"
   
   # ========== 共通関数 ==========
   function_name() {
       # implementation
   }
   ```

## Key Principles
- Templates are blueprints, not ready-to-run scripts
- All configurable options must be clearly marked
- Include error checking and validation functions
- Keep templates generic and reusable
- No hardcoded values except defaults

## Example
User: "Create a backup script template"
→ Create `backup.sh.template` with variables for SOURCE, DEST, etc.