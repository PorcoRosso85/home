"""Requirement Graph Logic - 要件グラフのインテリジェンスエンジン

使い方がわからない場合:
>>> from poc.requirement_graph_logic import help
>>> help()
"""

def help():
    """RGLの使い方を表示"""
    print("""
=== Requirement Graph Logic (RGL) クイックスタート ===

1分で使えるようになります:

>>> from poc.requirement_graph_logic import quick_start
>>> handler = quick_start()
>>> result = handler({"text": "認証機能を作る", "metadata": {}})
>>> print(result["scores"])

詳細は:
>>> from poc.requirement_graph_logic import show_examples
>>> show_examples()
""")


def quick_start():
    """最速で使い始める"""
    try:
        from .infrastructure.adapters import create_in_memory_repository, create_simple_embedder
        from .application.commands import create_add_requirement_handler
        
        repo = create_in_memory_repository()
        embedder = create_simple_embedder()
        handler = create_add_requirement_handler(repo, embedder)
        
        print("✅ セットアップ完了！使い方:")
        print('>>> result = handler({"text": "要件テキスト", "metadata": {}})')
        print('>>> print(result["scores"]) # スコアを確認')
        
        return handler
    except Exception as e:
        print(f"❌ エラー: {e}")
        print("\n必要なモジュール:")
        print(">>> from poc.requirement_graph_logic.infrastructure.adapters import create_in_memory_repository, create_simple_embedder")
        print(">>> from poc.requirement_graph_logic.application.commands import create_add_requirement_handler")
        raise


def show_examples():
    """実例を表示"""
    print("""
=== 実例集 ===

# 基本的な使い方
handler = quick_start()
result = handler({"text": "ユーザー認証機能", "metadata": {}})

# 結果の見方
if "error" in result:
    print(f"エラー: {result['error']}")
elif not result["requirement_id"]:
    print("重複のため追加されず")
else:
    print(f"追加成功: {result['requirement_id']}")
    print(f"スコア: {result['scores']}")

# スコアの意味
- uniqueness < 0.1: ほぼ重複
- clarity < 0.6: 曖昧
- completeness < 0.7: 不完全

# エラーになる例
handler("テキストだけ")  # ❌ 辞書が必要
handler({"text": "test"})  # ❌ metadataが必要
""")


__all__ = ["help", "quick_start", "show_examples"]