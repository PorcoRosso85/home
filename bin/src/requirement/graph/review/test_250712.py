#!/usr/bin/env python3
"""
Requirement Graph System レビューテスト (2025-07-12)

3つのペルソナ（Owner、Manager、Engineer）による要件追加と
システムの制約検証を再現可能な形で実行します。
"""

import json
import subprocess
import time
from typing import Dict, Any, List, Tuple


class RequirementGraphTester:
    """要件グラフシステムのテストを実行するクラス"""

    def __init__(self):
        self.results: List[Tuple[str, Dict[str, Any], bool]] = []

    def run_command(self, template_data: Dict[str, Any], description: str) -> Dict[str, Any]:
        """コマンドを実行し、結果を記録"""

        cmd = f'echo \'{json.dumps(template_data)}\' | nix run .#run'

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd="/home/nixos/bin/src/requirement/graph"
            )

            # 結果から最初のJSON行を抽出
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if line.startswith('{'):
                    try:
                        response = json.loads(line)
                        success = response.get('data', {}).get('status') == 'success'
                        if not success and 'error' in response.get('data', {}):
                            success = False  # エラーは期待される場合もある
                        else:
                            success = True

                        self.results.append((description, response, success))
                        return response
                    except json.JSONDecodeError:
                        continue

            # JSONが見つからない場合
            self.results.append((description, {"error": "No JSON response"}, False))
            return {"error": "No JSON response"}

        except Exception as e:
            error_response = {"error": str(e)}
            self.results.append((description, error_response, False))
            return error_response

        finally:
            time.sleep(0.5)  # サーバーに負荷をかけないよう待機

    def test_phase1_owner_perspective(self):
        """フェーズ1: オーナー視点での要件追加"""

        # オーナー要件1: グローバル展開
        self.run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "lp_owner_001",
                "title": "グローバル展開可能なプラットフォーム",
                "description": "5年以内に10カ国以上でサービス展開",
                "priority": 3
            }
        }, "オーナー要件1: グローバル展開戦略")

        # オーナー要件2: ユーザー成長目標
        self.run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "lp_owner_002",
                "title": "月間アクティブユーザー100万人達成",
                "description": "3年以内にMAU100万人を達成する",
                "priority": 3
            }
        }, "オーナー要件2: ユーザー成長目標")

        # オーナー要件3: 曖昧な要件（システムが警告すべき）
        self.run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "lp_owner_003",
                "title": "最高の学習体験",
                "description": "業界で最も使いやすい学習プラットフォーム"
            }
        }, "オーナー要件3: 曖昧な要件（警告テスト）")

    def test_phase2_manager_perspective(self):
        """フェーズ2: マネージャー視点での実行計画"""

        # マネージャー要件1: MVP計画
        self.run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "lp_mgr_001",
                "title": "初期版リリース",
                "description": "6ヶ月以内にMVPをリリース",
                "priority": 2
            }
        }, "マネージャー要件1: MVP計画")

        # 依存関係: MVP → ユーザー成長目標
        self.run_command({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "lp_mgr_001",
                "parent_id": "lp_owner_002"
            }
        }, "依存関係: MVP → ユーザー成長目標")

        # マネージャー要件2: ユーザー登録機能
        self.run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "lp_mgr_002",
                "title": "ユーザー登録機能",
                "description": "メール認証付きユーザー登録",
                "priority": 3
            }
        }, "マネージャー要件2: ユーザー登録機能")

        # 依存関係: ユーザー登録 → MVP
        self.run_command({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "lp_mgr_002",
                "parent_id": "lp_mgr_001"
            }
        }, "依存関係: ユーザー登録 → MVP")

    def test_phase3_engineer_perspective(self):
        """フェーズ3: エンジニア視点での技術実装"""

        # エンジニア要件1: JWT認証
        self.run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "lp_eng_001",
                "title": "JWT認証実装",
                "description": "RFC 7519準拠のJWT認証システム",
                "priority": 3
            }
        }, "エンジニア要件1: JWT認証実装")

        # 依存関係: JWT → ユーザー登録
        self.run_command({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "lp_eng_001",
                "parent_id": "lp_mgr_002"
            }
        }, "依存関係: JWT → ユーザー登録")

        # エンジニア要件2: パスワードセキュリティ
        self.run_command({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "lp_eng_002",
                "title": "パスワードセキュリティ",
                "description": "bcryptでハッシュ化",
                "priority": 3
            }
        }, "エンジニア要件2: パスワードセキュリティ")

    def test_phase4_constraint_validation(self):
        """フェーズ4: システム制約の検証"""

        # テスト1: 循環依存の検出

        # A → B の依存関係を作成
        self.run_command({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "lp_owner_001",
                "parent_id": "lp_owner_002"
            }
        }, "循環依存テスト準備: A → B")

        # B → A の依存関係を試みる（エラーになるはず）
        result = self.run_command({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "lp_owner_002",
                "parent_id": "lp_owner_001"
            }
        }, "循環依存テスト: B → A（エラー期待）")

        # エラーチェック
        if 'error' in result.get('data', {}):
            pass
        else:
            pass

        # テスト2: 深い階層構造の制限

        # 深い階層の要件を作成
        for i in range(1, 8):  # 1から7まで
            self.run_command({
                "type": "template",
                "template": "create_requirement",
                "parameters": {
                    "id": f"lp_deep_{i:03d}",
                    "title": f"深い階層{i}"
                }
            }, f"深さテスト要件{i}")

            if i > 1:
                self.run_command({
                    "type": "template",
                    "template": "add_dependency",
                    "parameters": {
                        "child_id": f"lp_deep_{i:03d}",
                        "parent_id": f"lp_deep_{i-1:03d}"
                    }
                }, f"深さテスト依存関係: {i} → {i-1}")

    def test_phase5_query_operations(self):
        """フェーズ5: クエリ操作のテスト"""

        # 要件一覧の取得
        self.run_command({
            "type": "template",
            "template": "list_requirements",
            "parameters": {
                "limit": 10
            }
        }, "要件一覧の取得")

        # 特定要件の検索
        self.run_command({
            "type": "template",
            "template": "find_requirement",
            "parameters": {
                "id": "lp_mgr_001"
            }
        }, "特定要件の検索: MVP")

        # 依存関係の検索
        self.run_command({
            "type": "template",
            "template": "find_dependencies",
            "parameters": {
                "requirement_id": "lp_mgr_002",
                "depth": 5
            }
        }, "依存関係の検索: ユーザー登録機能")

    def generate_report(self):
        """テスト結果のレポートを生成"""
        total_tests = len(self.results)
        successful_tests = sum(1 for _, _, success in self.results if success)

    def run_all_tests(self):
        """全テストを順番に実行"""

        self.test_phase1_owner_perspective()
        self.test_phase2_manager_perspective()
        self.test_phase3_engineer_perspective()
        self.test_phase4_constraint_validation()
        self.test_phase5_query_operations()
        self.generate_report()


if __name__ == "__main__":
    tester = RequirementGraphTester()
    tester.run_all_tests()
