#!/usr/bin/env bash
set -e

# @describe ツール作成方法のヘルプを提供します。新しいツールを追加する手順とBash、Python、JavaScriptでの実装の違いを説明します。ツールは /home/nixos/bin/src/tools ディレクトリに格納されています。
# @option --language![bash|python|javascript] 情報を取得したい言語を指定します
# @flag --show-examples 各言語のサンプルコードも表示します

# @env LLM_OUTPUT=/dev/stdout The output path

main() {
    local language="${argc_language}"
    local show_examples="${argc_show_examples}"
    
    # ツールディレクトリのパスを動的に取得
    TOOL_DIR="$(cd "$(dirname "$0")" && pwd)"
    TOOLS_TXT_PATH="$(dirname "$TOOL_DIR")/tools.txt"
    
    case "$language" in
        bash)
            cat <<'EOF' > "$LLM_OUTPUT"
※Bash, Python, Javascriptのうちどの言語でもツールを作成することが可能です。

# Bashでのツール作成方法

Bashでツールを作成する場合は、argc構文が**必須**です。

## 主な要素:

0. **shebang**
  以下を基本とする
  `!/usr/bin/env bash`

  ケースによってはnixを使用し、ツール内の依存関係を解決する
  `!/usr/bin/env -S nix shell nixpkgs#<package used in this tool> --command bash`
  
  複数の依存関係が必要な場合は、空白で区切って指定する
  `!/usr/bin/env -S nix shell nixpkgs#package1 nixpkgs#package2 --command bash`
  
  例: argcとrcloneを共に使用するツールの場合
  `!/usr/bin/env -S nix shell nixpkgs#rclone nixpkgs#argc --command bash`

1. **特殊コメントタグ**:
   - `# @describe`: ツールの説明（必須）
   - `# @option`: パラメータの定義
   - `# @flag`: ブールフラグの定義

2. **パラメータの構文**:
   - 必須パラメータ: `# @option --name! 説明`
   - オプションパラメータ: `# @option --name 説明`
   - 列挙型: `# @option --name![value1|value2] 説明`
   - 整数型: `# @option --name! <INT> 説明`
   - 数値型: `# @option --name! <NUM> 説明`
   - 配列: `# @option --name+ <VALUE> 説明` (必須配列)
   - オプション配列: `# @option --name* 説明`
   - ブールフラグ: `# @flag --name 説明`

3. **スクリプト終了時の必須行**:
   ```bash
   eval "$(argc --argc-eval "$0" "$@")"
   ```

4. **パラメータへのアクセス**:
   - `${argc_パラメータ名}` の形式で変数にアクセス
   - 配列の場合は `${argc_配列名[@]}` でアクセス
EOF

            if [ "$show_examples" = "true" ]; then
                cat <<'EOF' >> "$LLM_OUTPUT"

## Bashツールの例:
```bash
#!/usr/bin/env bash
set -e

\# @describe 天気情報を取得します
\# @option --location! 天気を取得したい場所の名前
\# @option --units[metric|imperial|standard] 温度単位（デフォルト: metric）
\# @flag --detailed 詳細な天気情報を表示する

\# @env LLM_OUTPUT=/dev/stdout 出力先

main() {
    local location="${argc_location}"
    local units="${argc_units:-metric}"
    local detailed="${argc_detailed}"
    
    # ここに実際の処理を書く
    if [ "$detailed" = "true" ]; then
        echo "詳細な天気情報: $location ($units)" > "$LLM_OUTPUT"
    else
        echo "天気情報: $location ($units)" > "$LLM_OUTPUT"
    fi
}

eval "$(argc --argc-eval "$0" "$@")"
```
EOF
            fi
            ;;
            
        python)
            cat <<'EOF' > "$LLM_OUTPUT"
# Pythonでのツール作成方法

Pythonでツールを作成する場合は、**argc構文は不要**です。標準的なPythonの型ヒントとdocstringを使います。

## 主な要素:

0. **shebang**
  必ず以下のshebangを使用する（nixを使用してpythonを確実に利用可能にする）
  `#!/usr/bin/env -S nix run nixpkgs#python3 --`
  
  依存パッケージが必要な場合は、ファイル内で明示的にインポートすること

1. **関数定義**:
   - `run` という名前の関数を定義する
   - 型ヒントを使用してパラメータの型を指定

2. **パラメータの定義**:
   - 必須パラメータ: 通常の引数
   - オプションパラメータ: デフォルト値付きの引数（`param: str = None`）
   - 列挙型: `Literal` を使用（`param: Literal["option1", "option2"]`）
   - 配列: `List[type]` を使用（`param: List[str]`）
   - オプション配列: `Optional[List[type]]`（`param: Optional[List[str]] = None`）

3. **docstring**:
   - 関数の説明
   - `Args:` セクションで各パラメータの説明

4. **戻り値**:
   - 関数の戻り値が出力として使われる
EOF

            if [ "$show_examples" = "true" ]; then
                cat <<'EOF' >> "$LLM_OUTPUT"

## Pythonツールの例:
```python
from typing import List, Literal, Optional

def run(
    location: str,
    units: Literal["metric", "imperial", "standard"] = "metric",
    detailed: bool = False
):
    """天気情報を取得します
    Args:
        location: 天気を取得したい場所の名前
        units: 温度単位（metric, imperial, standard）
        detailed: 詳細な天気情報を表示する
    """
    # ここに実際の処理を書く
    if detailed:
        return f"詳細な天気情報: {location} ({units})"
    else:
        return f"天気情報: {location} ({units})"
```
EOF
            fi
            ;;
            
        javascript)
            cat <<'EOF' > "$LLM_OUTPUT"
# JavaScriptでのツール作成方法

JavaScriptでツールを作成する場合は、**argc構文は不要**です。JSDocコメントを使用します。

## 主な要素:

0. **shebang**
  必ず以下のshebangを使用する（nixを使用してnodeを確実に利用可能にする）
  `#!/usr/bin/env -S nix run nixpkgs#nodejs_22 --`
  
  依存パッケージが必要な場合は、ファイル内でrequireして明示的にインポートすること

1. **関数のエクスポート**:
   - CommonJS: `exports.run = function(args) {...}`
   - または ESM: `export function run(args) {...}`

2. **JSDocコメント**:
   - 関数の説明
   - `@typedef {Object} Args` でパラメータオブジェクトの型を定義
   - `@property {type} name - description` で各パラメータを定義

3. **パラメータの定義**:
   - 必須パラメータ: `@property {type} name - description`
   - オプションパラメータ: `@property {type} [name] - description`
   - 列挙型: `@property {'option1'|'option2'} name - description`
   - 整数型: `@property {Integer} name - description`
   - 数値型: `@property {number} name - description`
   - 配列: `@property {type[]} name - description`

4. **パラメータへのアクセス**:
   - 関数は単一のオブジェクトを受け取る
   - `args.paramName` の形でパラメータにアクセス
EOF

            if [ "$show_examples" = "true" ]; then
                cat <<'EOF' >> "$LLM_OUTPUT"

## JavaScriptツールの例:
```javascript
/**
 * 天気情報を取得します
 * @typedef {Object} Args
 * @property {string} location - 天気を取得したい場所の名前
 * @property {'metric'|'imperial'|'standard'} [units='metric'] - 温度単位
 * @property {boolean} [detailed=false] - 詳細な天気情報を表示する
 * @param {Args} args
 */
exports.run = function (args) {
  // ここに実際の処理を書く
  if (args.detailed) {
    return `詳細な天気情報: ${args.location} (${args.units || 'metric'})`;
  } else {
    return `天気情報: ${args.location} (${args.units || 'metric'})`;
  }
}
```
EOF
            fi
            ;;
    esac
    
    # 重要な規約
    cat <<'EOF' >> "$LLM_OUTPUT"

## 重要な規約:

1. **ヘルプと説明**:
   - argcによるヘルプ文は可能な限り詳細に記述すること
   - パラメータの説明、使用例、制限事項などを明記すること
   - パラメータの名前とその目的を明確にすること
   - ツール自体に改善や詳細化の指示があった場合は、この文書に記載を追加すること

2. **スクリプトの設計**:
   - 各ツールスクリプトはファイル単体で動作するよう設計すること
   - 必要な依存関係がある場合は、適切なshebangで解決すること
   - 必要に応じて実行時のエラーチェックを行うこと
   - nix shellを使用する場合は `#!/usr/bin/env -S nix shell nixpkgs#パッケージ名 --command bash` 形式を使用すること
   - ツールが外部コマンドに依存する場合は、スクリプト自身がshebangで依存関係を解決できるようにすること（例: rcloneを使用するツールは自身でrcloneパッケージを導入する）

3. **エラーハンドリング**:
   - 適切なエラーハンドリングを実装すること
   - わかりやすいエラーメッセージを表示すること
   - 引数の検証を適切に行うこと

4. **ユーザーインターフェース**:
   - 重要な操作（削除など）の前に確認メッセージを表示すること
   - 実行中の進捗状況や結果を適切に表示すること
   - --verbose フラグがある場合は詳細な情報を提供すること
EOF
    
    # ツールディレクトリのパスを動的に取得したものを利用
    cat <<EOF >> "$LLM_OUTPUT"

## ツール追加の手順:

1. ツールファイルを \`${TOOL_DIR}\` ディレクトリに作成
   - 例: \`${TOOL_DIR}/my_new_tool.sh\`
2. 作成したファイルに実行権限を付与
   - \`chmod +x ${TOOL_DIR}/my_new_tool.sh\`
3. \`${TOOLS_TXT_PATH}\` にツール名を追加
4. \`argc build\` を実行してツールをビルド
5. \`argc check\` で問題がないか確認

* 無事ビルドが完了できたかどうかは、 argc buildによる出力とfunctions.jsonを確認すること
* エラーなくjsonに新たなツールが追加されていればビルドが無事完了している

ツール作成の詳細は \`docs/tool.md\` を参照してください。
新しいツールはアプリケーション再起動後に利用可能になります。
EOF
}

eval "$(argc --argc-eval "$0" "$@")"