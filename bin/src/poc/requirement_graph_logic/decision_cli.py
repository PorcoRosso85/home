"""開発決定事項管理CLI - RGLを使った決定ログ"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from .infrastructure.persistence import create_file_repository
from .infrastructure.adapters import create_simple_embedder
from .application.commands import create_add_requirement_handler


class DecisionManager:
    """開発決定事項マネージャー"""
    
    def __init__(self, file_path: str = None):
        """
        Args:
            file_path: 決定事項の保存先（デフォルト: ~/.rgl/decisions.jsonl）
        """
        # 環境変数からファイルパスを取得
        if file_path is None:
            file_path = os.environ.get('RGL_FILE')
        
        # 永続化リポジトリとエンベッダーを初期化
        self.repo = create_file_repository(file_path)
        self.embedder = create_simple_embedder(dimension=50)  # より高次元で精度向上
        self.add_handler = create_add_requirement_handler(self.repo, self.embedder)
        
        # 統計情報を表示
        stats = self.repo.get_stats()
        print(f"📂 決定事項ファイル: {stats['file_path']}")
        print(f"📊 既存の決定事項: {stats['total']}件")
        if stats['total'] > 0:
            print(f"   最古: {stats['oldest']}")
            print(f"   最新: {stats['newest']}")
        print()
    
    def add_decision(self, text: str, metadata: Optional[Dict] = None) -> Dict:
        """新しい決定事項を追加"""
        if metadata is None:
            metadata = {}
        
        # タイムスタンプを自動追加
        metadata['timestamp'] = datetime.now().isoformat()
        metadata['type'] = metadata.get('type', 'decision')
        
        # RGLで品質評価と重複チェック
        result = self.add_handler({
            "text": text,
            "metadata": metadata
        })
        
        return result
    
    def list_decisions(self, limit: int = 10) -> List[Dict]:
        """最近の決定事項を表示"""
        all_decisions = self.repo.get_all()
        
        # 日付でソート（新しい順）
        sorted_decisions = sorted(
            all_decisions,
            key=lambda x: x['created_at'],
            reverse=True
        )
        
        return sorted_decisions[:limit]
    
    def search_similar(self, query: str, limit: int = 5) -> List[Dict]:
        """類似の決定事項を検索"""
        # クエリの埋め込みを生成
        embed_result = self.embedder.embed(query)
        if "error" in embed_result:
            return []
        
        # 類似検索
        similar = self.repo.find_similar(embed_result, limit=limit)
        if isinstance(similar, dict) and "error" in similar:
            return []
        
        return similar


def format_decision(decision: Dict, index: int = None) -> str:
    """決定事項を読みやすくフォーマット"""
    lines = []
    if index is not None:
        lines.append(f"\n[{index}] {decision['text']}")
    else:
        lines.append(f"\n{decision['text']}")
    
    lines.append(f"   ID: {decision['id']}")
    lines.append(f"   日時: {decision['created_at']}")
    
    metadata = decision.get('metadata', {})
    if metadata.get('type'):
        lines.append(f"   タイプ: {metadata['type']}")
    if metadata.get('tags'):
        lines.append(f"   タグ: {', '.join(metadata['tags'])}")
    
    return '\n'.join(lines)


def main():
    """CLIのメインエントリーポイント"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='開発決定事項管理ツール - RGLベース',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  # 新しい決定事項を追加
  %(prog)s add "認証機能にJWTを使用することに決定"
  
  # タグ付きで追加
  %(prog)s add "DBをPostgreSQLからKuzuDBに移行" --tags architecture,database
  
  # 最近の決定事項を表示
  %(prog)s list
  
  # 類似の決定事項を検索
  %(prog)s search "認証"
  
  # 統計情報を表示
  %(prog)s stats
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='コマンド')
    
    # add コマンド
    add_parser = subparsers.add_parser('add', help='新しい決定事項を追加')
    add_parser.add_argument('text', help='決定事項の内容')
    add_parser.add_argument('--type', default='decision', 
                          choices=['decision', 'problem', 'solution', 'todo'],
                          help='決定事項のタイプ')
    add_parser.add_argument('--tags', help='カンマ区切りのタグ')
    
    # list コマンド
    list_parser = subparsers.add_parser('list', help='最近の決定事項を表示')
    list_parser.add_argument('-n', '--number', type=int, default=10,
                           help='表示件数（デフォルト: 10）')
    
    # search コマンド
    search_parser = subparsers.add_parser('search', help='類似の決定事項を検索')
    search_parser.add_argument('query', help='検索クエリ')
    search_parser.add_argument('-n', '--number', type=int, default=5,
                             help='表示件数（デフォルト: 5）')
    
    # stats コマンド
    stats_parser = subparsers.add_parser('stats', help='統計情報を表示')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # マネージャーを初期化
    manager = DecisionManager()
    
    if args.command == 'add':
        # メタデータを構築
        metadata = {'type': args.type}
        if args.tags:
            metadata['tags'] = [tag.strip() for tag in args.tags.split(',')]
        
        # 決定事項を追加
        result = manager.add_decision(args.text, metadata)
        
        if "error" in result:
            print(f"❌ エラー: {result['error']}")
            return
        
        # 結果を表示
        if result['requirement_id']:
            print(f"✅ 決定事項を追加しました")
            print(f"   ID: {result['requirement_id']}")
        else:
            print("⚠️ 重複の可能性があります")
        
        # スコアを表示
        scores = result['scores']
        print(f"\n📊 品質スコア:")
        print(f"   独自性: {scores['uniqueness']:.2f}")
        print(f"   明確性: {scores['clarity']:.2f}")
        print(f"   完全性: {scores['completeness']:.2f}")
        
        # 類似決定事項があれば表示
        if result['similar_requirements']:
            print(f"\n🔍 類似の決定事項:")
            for similar in result['similar_requirements'][:3]:
                print(f"   - {similar['text']} (類似度: {similar['similarity']:.2f})")
        
        # 提案があれば表示
        if result['suggestions']:
            print(f"\n💡 改善提案:")
            for suggestion in result['suggestions']:
                print(f"   - {suggestion}")
    
    elif args.command == 'list':
        decisions = manager.list_decisions(limit=args.number)
        if not decisions:
            print("決定事項がまだありません")
            return
        
        print(f"📋 最近の決定事項（{len(decisions)}件）:")
        for i, decision in enumerate(decisions, 1):
            print(format_decision(decision, i))
    
    elif args.command == 'search':
        results = manager.search_similar(args.query, limit=args.number)
        if not results:
            print(f"「{args.query}」に関連する決定事項は見つかりませんでした")
            return
        
        print(f"🔍 「{args.query}」に関連する決定事項（{len(results)}件）:")
        for i, decision in enumerate(results, 1):
            print(format_decision(decision, i))
    
    elif args.command == 'stats':
        stats = manager.repo.get_stats()
        all_decisions = manager.repo.get_all()
        
        print("📊 統計情報:")
        print(f"   総決定事項数: {stats['total']}件")
        
        if stats['total'] > 0:
            print(f"   期間: {stats['oldest']} 〜 {stats['newest']}")
            
            # タイプ別統計
            type_counts = {}
            for decision in all_decisions:
                dtype = decision.get('metadata', {}).get('type', 'decision')
                type_counts[dtype] = type_counts.get(dtype, 0) + 1
            
            print(f"\n   タイプ別:")
            for dtype, count in sorted(type_counts.items()):
                print(f"     {dtype}: {count}件")
            
            # タグ統計
            tag_counts = {}
            for decision in all_decisions:
                tags = decision.get('metadata', {}).get('tags', [])
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            if tag_counts:
                print(f"\n   よく使われるタグ:")
                for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"     {tag}: {count}件")


if __name__ == "__main__":
    main()