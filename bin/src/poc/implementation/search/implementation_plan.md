# ctags統合実装計画

## アーキテクチャ

```
search/
├── search.py              # メインインターフェース
├── providers/
│   ├── __init__.py
│   ├── base.py           # 抽象基底クラス
│   ├── ctags_provider.py # ctagsラッパー
│   └── regex_provider.py # フォールバック実装
├── models.py             # SearchResult, Symbol型定義
└── utils.py              # 共通ユーティリティ
```

## 実装手順

### 1. プロバイダーインターフェース定義
```python
# providers/base.py
from abc import ABC, abstractmethod
from typing import List
from ..models import SearchResult

class SymbolProvider(ABC):
    @abstractmethod
    def search(self, path: str) -> SearchResult:
        """シンボルを検索"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """プロバイダーが利用可能か確認"""
        pass
```

### 2. ctags プロバイダー実装
```python
# providers/ctags_provider.py
import subprocess
import json
from pathlib import Path
from .base import SymbolProvider
from ..models import SearchResult, Symbol

class CtagsProvider(SymbolProvider):
    def __init__(self):
        self.ctags_cmd = self._find_ctags()
    
    def is_available(self) -> bool:
        return self.ctags_cmd is not None
    
    def search(self, path: str) -> SearchResult:
        try:
            # Universal Ctagsの--output-format=jsonを使用
            result = subprocess.run(
                [self.ctags_cmd, '--output-format=json', '-f', '-', path],
                capture_output=True,
                text=True,
                check=True
            )
            
            symbols = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    tag = json.loads(line)
                    symbols.append(self._convert_to_symbol(tag))
            
            return SearchResult(
                success=True,
                data=symbols,
                metadata={
                    'provider': 'ctags',
                    'searched_files': len(set(s.path for s in symbols))
                }
            )
        except Exception as e:
            return SearchResult(
                success=False,
                error=f"ctags error: {str(e)}"
            )
```

### 3. 統合ポイント

```python
# search.py
from .providers.ctags_provider import CtagsProvider
from .providers.regex_provider import RegexProvider

_providers = {
    'ctags': CtagsProvider(),
    'regex': RegexProvider()
}

def search_symbols(path: str, provider: str = "auto") -> SearchResult:
    """
    統一インターフェース
    provider: "auto", "ctags", "regex"
    """
    if provider == "auto":
        # ctagsが利用可能ならそれを使う
        for name in ['ctags', 'regex']:
            if _providers[name].is_available():
                return _providers[name].search(path)
    else:
        return _providers[provider].search(path)
```

## 利点

1. **段階的移行** - 既存のテストを壊さずにctags統合
2. **フォールバック** - ctagsがない環境でも動作
3. **拡張性** - 新しいプロバイダーを追加可能
4. **テスト容易性** - プロバイダーをモック化できる

## 次のステップ

1. `models.py` でSearchResult, Symbol型を実装
2. `providers/base.py` で基底クラス実装
3. `providers/ctags_provider.py` でctags統合
4. 既存のテストをグリーンにする