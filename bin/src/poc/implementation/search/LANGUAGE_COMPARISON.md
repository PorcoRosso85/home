# ctags統合のための言語選択比較

## 評価基準
1. ctagsとの統合性
2. エラーハンドリング
3. テストの書きやすさ
4. パフォーマンス
5. 依存関係管理

## 言語比較

### Python ⭐⭐⭐⭐⭐ (推奨)
```python
# 実装イメージ
class CtagsSearchProvider:
    def search_symbols(self, path: str) -> SearchResult:
        try:
            tags = subprocess.run(['ctags', '-f', '-', '--output-format=json'], ...)
            return self._parse_tags(tags.stdout)
        except Exception as e:
            return SearchResult(success=False, error=str(e))
```

**利点:**
- ✅ subprocessモジュールでctags制御が容易
- ✅ 既存のtest_search.pyとシームレスに統合
- ✅ 型ヒントで堅牢性確保
- ✅ JSON処理が標準ライブラリ
- ✅ 例外処理が成熟

**欠点:**
- ❌ 実行速度は中程度

### Go ⭐⭐⭐⭐
```go
type CtagsProvider struct {
    executable string
}

func (p *CtagsProvider) SearchSymbols(path string) (*SearchResult, error) {
    cmd := exec.Command(p.executable, "-f", "-", "--output-format=json", path)
    output, err := cmd.Output()
    // ...
}
```

**利点:**
- ✅ 高速実行
- ✅ シングルバイナリ配布
- ✅ 並行処理が得意
- ✅ エラーハンドリングが明示的

**欠点:**
- ❌ 既存のPythonテストと統合が複雑
- ❌ ビルドステップが必要

### TypeScript ⭐⭐⭐
```typescript
class CtagsSearchProvider {
    async searchSymbols(path: string): Promise<SearchResult> {
        try {
            const { stdout } = await execa('ctags', ['-f', '-', '--output-format=json', path]);
            return this.parseTags(stdout);
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}
```

**利点:**
- ✅ 非同期処理が自然
- ✅ 型安全性
- ✅ npmエコシステム

**欠点:**
- ❌ Node.js依存
- ❌ Pythonテストとの統合が困難

### Bash ⭐⭐
```bash
search_symbols() {
    local path="$1"
    local tags_output
    
    if tags_output=$(ctags -f - --output-format=json "$path" 2>&1); then
        echo "$tags_output" | jq '{ success: true, data: . }'
    else
        echo "{ \"success\": false, \"error\": \"$tags_output\" }"
    fi
}
```

**利点:**
- ✅ 依存なし
- ✅ シンプル

**欠点:**
- ❌ エラーハンドリングが弱い
- ❌ 複雑な処理が困難
- ❌ テストが書きにくい

### Nushell ⭐⭐
```nu
def search-symbols [path: string] {
    try {
        let tags = (^ctags -f - --output-format=json $path | from json)
        {success: true, data: $tags}
    } catch {
        {success: false, error: $"ctags failed: ($in)"}
    }
}
```

**利点:**
- ✅ データ処理が得意
- ✅ パイプライン処理

**欠点:**
- ❌ Nu環境限定
- ❌ エコシステムが小さい

## 結論

**Python が最適** な理由：

1. **既存コードとの統合性**
   - test_search.py がすでにPython
   - SearchResult型がPythonで定義済み
   - 同じ言語なら直接importできる

2. **実装の容易さ**
   ```python
   # search.py に追加するだけ
   from .providers.ctags_provider import CtagsProvider
   from .providers.regex_provider import RegexProvider
   
   def search_symbols(path: str, provider="auto") -> SearchResult:
       if provider == "auto" and ctags_available():
           return CtagsProvider().search(path)
       return RegexProvider().search(path)
   ```

3. **テストの統一性**
   - 既存のpytestフレームワークを活用
   - モックが簡単

4. **エラーハンドリング**
   - 例外処理が成熟
   - 統一されたSearchResult形式で返却

Goは性能面で優れているが、既存のPythonコードベースとの統合コストが高すぎるため、Pythonが現実的な選択です。