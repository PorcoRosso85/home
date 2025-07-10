"""
Requirement Validator - 要件品質検証
依存: domain
外部依存: なし

要件の曖昧性、測定可能性、完了条件の明確性等を検証
"""
from typing import Dict, Optional
import re


class RequirementValidator:
    """
    要件の品質を多角的に検証
    人間が要件追加時に考慮する観点を実装
    """

    def __init__(self):
        # 曖昧な表現のパターン
        self.ambiguous_terms = {
            "速い", "遅い", "早い",
            "使いやすい", "分かりやすい", "見やすい",
            "効率的", "効果的", "適切な", "十分な",
            "良い", "悪い", "多い", "少ない",
            "簡単", "複雑", "シンプル",
            "できるだけ", "なるべく", "可能な限り"
        }

        # 測定可能にすべき表現
        self.measurable_aspects = {
            "パフォーマンス": ["レスポンスタイム", "スループット", "レイテンシ"],
            "容量": ["ストレージ", "メモリ", "帯域幅"],
            "可用性": ["稼働率", "MTBF", "MTTR"],
            "ユーザビリティ": ["タスク完了時間", "エラー率", "学習曲線"]
        }

    def validate_clarity(self, requirement_text: str) -> Dict[str, any]:
        """
        要件の明確性を検証
        
        Args:
            requirement_text: 要件の説明文
            
        Returns:
            検証結果（is_valid, score, errors, suggestions）
        """
        errors = []
        suggestions = []

        # 曖昧な表現をチェック
        found_ambiguous = []
        for term in self.ambiguous_terms:
            if term in requirement_text:
                found_ambiguous.append(term)

        if found_ambiguous:
            errors.append(f"曖昧な表現が含まれています: {', '.join(found_ambiguous)}")
            suggestions.append("定量的・具体的な基準に置き換えてください")

            # 具体的な改善例を提示
            if "速い" in found_ambiguous:
                suggestions.append("例: 「速い」→「200ms以内に応答」")
            if "使いやすい" in found_ambiguous:
                suggestions.append("例: 「使いやすい」→「3クリック以内で主要機能にアクセス可能」")

        is_valid = len(errors) == 0
        score = -0.5 if errors else 0.0

        return {
            "is_valid": is_valid,
            "score": score,
            "errors": errors,
            "suggestions": suggestions
        }

    def validate_measurability(self, requirement: Dict) -> Dict[str, any]:
        """
        測定可能性を検証
        
        Args:
            requirement: 要件データ
            
        Returns:
            検証結果
        """
        errors = []
        suggestions = []

        description = requirement.get("description", "")

        # 数値目標の有無をチェック
        has_numeric = bool(re.search(r'\d+(\.\d+)?[%％]?|[０-９]+', description))

        # 改善・向上系の表現をチェック
        improvement_terms = ["改善", "向上", "削減", "短縮", "増加", "減少"]
        has_improvement = any(term in description for term in improvement_terms)

        if has_improvement and not has_numeric:
            errors.append("改善目標に数値基準がありません")
            suggestions.append("現状値と目標値を明記してください（例：現状5秒→目標2秒）")

        # 比較表現のチェック
        comparison_terms = ["より", "以上", "以下", "未満", "超える"]
        has_comparison = any(term in description for term in comparison_terms)

        if has_comparison and not has_numeric:
            errors.append("比較基準が不明確です")
            suggestions.append("具体的な数値や基準を設定してください")

        is_valid = len(errors) == 0
        score = -0.3 if errors else 0.0

        return {
            "is_valid": is_valid,
            "score": score,
            "errors": errors,
            "suggestions": suggestions
        }

    def validate_completeness(self, requirement: Dict) -> Dict[str, any]:
        """
        完了条件（Definition of Done）の明確性を検証
        
        Args:
            requirement: 要件データ
            
        Returns:
            検証結果
        """
        errors = []
        suggestions = []

        # 完了条件のキーワード
        done_keywords = [
            "完了条件", "完成条件", "受け入れ基準",
            "Definition of Done", "DoD", "acceptance criteria"
        ]

        description = requirement.get("description", "")
        has_done_criteria = any(keyword in description for keyword in done_keywords)

        if not has_done_criteria:
            # 機能要件の場合は完了条件が必須
            if requirement.get("requirement_type") == "functional":
                errors.append("完了条件が定義されていません")
                suggestions.append(
                    "以下の観点で完了条件を追加してください:\n"
                    "- 機能の動作確認方法\n"
                    "- エラーハンドリング\n"
                    "- テストケース"
                )

        # 曖昧な完了条件のチェック
        vague_done_terms = ["動作する", "問題ない", "正常に", "ちゃんと"]
        if has_done_criteria and any(term in description for term in vague_done_terms):
            errors.append("完了条件が曖昧です")
            suggestions.append("検証可能な具体的な条件を記載してください")

        is_valid = len(errors) == 0
        score = -0.4 if errors else 0.0

        return {
            "is_valid": is_valid,
            "score": score,
            "errors": errors,
            "suggestions": suggestions
        }

    def validate_terminology(self, requirement_text: str, glossary: Optional[Dict[str, str]] = None) -> Dict[str, any]:
        """
        用語の統一性を検証
        
        Args:
            requirement_text: 要件テキスト
            glossary: 用語集（キー：正式用語、値：同義語リスト）
            
        Returns:
            検証結果
        """
        errors = []
        suggestions = []

        # デフォルト用語集
        if glossary is None:
            glossary = {
                "ユーザー": ["利用者", "使用者", "ユーザ"],
                "システム": ["アプリケーション", "アプリ", "サービス"],
                "データベース": ["DB", "ＤＢ"],
                "API": ["ＡＰＩ", "api"]
            }

        # 同義語の混在をチェック
        for official_term, synonyms in glossary.items():
            found_terms = []
            if official_term in requirement_text:
                found_terms.append(official_term)
            for synonym in synonyms:
                if synonym in requirement_text:
                    found_terms.append(synonym)

            if len(found_terms) > 1:
                errors.append(f"用語が統一されていません: {', '.join(found_terms)}")
                suggestions.append(f"「{official_term}」に統一してください")

        # 略語の初出チェック
        abbreviations = re.findall(r'\b[A-Z]{2,}\b', requirement_text)
        for abbr in abbreviations:
            # 略語の説明があるかチェック
            pattern = f"{abbr}[（(][^）)]+[）)]"
            if not re.search(pattern, requirement_text):
                # 用語集に定義済みでもない場合のみエラー
                if abbr not in glossary and all(abbr not in synonyms for synonyms in glossary.values()):
                    errors.append(f"略語「{abbr}」の説明がありません")
                    suggestions.append("初出時に正式名称を併記してください")

        is_valid = len(errors) == 0
        score = -0.2 if errors else 0.0

        return {
            "is_valid": is_valid,
            "score": score,
            "errors": errors,
            "suggestions": suggestions
        }

    def validate_testability(self, requirement: Dict) -> Dict[str, any]:
        """
        テスト可能性を検証
        
        Args:
            requirement: 要件データ
            
        Returns:
            検証結果
        """
        errors = []
        suggestions = []

        description = requirement.get("description", "")

        # テスト関連キーワード
        test_keywords = ["テスト", "検証", "確認方法", "test", "verify"]
        has_test_mention = any(keyword in description.lower() for keyword in test_keywords)

        if not has_test_mention and requirement.get("requirement_type") == "functional":
            errors.append("テスト方法が記載されていません")
            suggestions.append(
                "以下を追加してください:\n"
                "- 正常系のテストケース\n"
                "- 異常系のテストケース\n"
                "- 自動テストの可否"
            )

        # 主観的な成功基準
        subjective_success = ["満足", "快適", "スムーズ", "自然な"]
        if any(term in description for term in subjective_success):
            errors.append("成功基準が主観的です")
            suggestions.append("客観的に測定可能な基準を設定してください")

        is_valid = len(errors) == 0
        score = -0.3 if errors else 0.0

        return {
            "is_valid": is_valid,
            "score": score,
            "errors": errors,
            "suggestions": suggestions
        }

    def validate_nonfunctional_requirements(self, requirement: Dict, requirement_type: str) -> Dict[str, any]:
        """
        非機能要件の考慮を検証
        
        Args:
            requirement: 要件データ
            requirement_type: 要件のタイプ（API, UI, Batch等）
            
        Returns:
            検証結果
        """
        errors = []
        suggestions = []

        description = requirement.get("description", "")

        # タイプ別必須非機能要件
        required_nfr = {
            "API": ["レスポンスタイム", "同時接続数", "エラーハンドリング"],
            "UI": ["画面表示時間", "ユーザビリティ", "アクセシビリティ"],
            "Batch": ["処理時間", "エラーリカバリ", "リトライ"],
            "Security": ["認証", "認可", "暗号化"]
        }

        if requirement_type in required_nfr:
            missing_nfr = []
            for nfr in required_nfr[requirement_type]:
                if nfr not in description:
                    missing_nfr.append(nfr)

            if missing_nfr:
                errors.append(f"必要な非機能要件が不足: {', '.join(missing_nfr)}")
                suggestions.append(f"{requirement_type}では以下の定義が推奨されます:\n" +
                                 "\n".join(f"- {nfr}" for nfr in missing_nfr))

        is_valid = len(errors) == 0
        score = -0.4 if errors else 0.0

        return {
            "is_valid": is_valid,
            "score": score,
            "errors": errors,
            "suggestions": suggestions
        }
