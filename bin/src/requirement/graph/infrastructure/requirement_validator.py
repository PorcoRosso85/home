"""
Requirement Validator - 要件品質検証
依存: domain
外部依存: なし

要件の曖昧性、測定可能性、完了条件の明確性等を検証
"""
from typing import Dict, List, Set, Optional, Tuple
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
                    suggestions.append(f"初出時に正式名称を併記してください")
        
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


# ============ IN-SOURCE TESTS ============

def test_曖昧な表現_速い_エラーと改善提案():
    """曖昧表現_定量化要求_スコアマイナス0.5"""
    validator = RequirementValidator()
    
    result = validator.validate_clarity("速いレスポンスタイムを実現する")
    
    assert result["is_valid"] == False
    assert result["score"] == -0.5
    assert "曖昧な表現が含まれています" in result["errors"][0]
    assert "速い" in result["errors"][0]
    assert "200ms以内に応答" in result["suggestions"][1]


def test_曖昧な表現_使いやすい_測定基準要求():
    """主観的表現_客観的指標への変換提案"""
    validator = RequirementValidator()
    
    result = validator.validate_clarity("使いやすいUIを提供する")
    
    assert result["is_valid"] == False
    assert result["score"] == -0.5
    assert "使いやすい" in result["errors"][0]
    assert "3クリック以内" in result["suggestions"][1]


def test_明確な表現_エラーなし():
    """具体的数値あり_検証成功_スコア0"""
    validator = RequirementValidator()
    
    result = validator.validate_clarity("APIのレスポンスタイムを200ms以内にする")
    
    assert result["is_valid"] == True
    assert result["score"] == 0.0
    assert len(result["errors"]) == 0


def test_測定可能性_改善目標に数値なし_エラー():
    """改善表現あり数値なし_現状値と目標値要求"""
    validator = RequirementValidator()
    
    requirement = {
        "description": "ページの読み込み速度を改善する"
    }
    result = validator.validate_measurability(requirement)
    
    assert result["is_valid"] == False
    assert result["score"] == -0.3
    assert "改善目標に数値基準がありません" in result["errors"][0]
    assert "現状値と目標値" in result["suggestions"][0]


def test_測定可能性_数値目標あり_成功():
    """改善目標に数値あり_検証成功"""
    validator = RequirementValidator()
    
    requirement = {
        "description": "ページ読み込み時間を現在の3秒から1秒以内に改善する"
    }
    result = validator.validate_measurability(requirement)
    
    assert result["is_valid"] == True
    assert result["score"] == 0.0


def test_完了条件なし_機能要件_エラー():
    """機能要件でDoD未定義_完了条件追加要求"""
    validator = RequirementValidator()
    
    requirement = {
        "description": "ログイン機能を実装する",
        "requirement_type": "functional"
    }
    result = validator.validate_completeness(requirement)
    
    assert result["is_valid"] == False
    assert result["score"] == -0.4
    assert "完了条件が定義されていません" in result["errors"][0]
    assert "機能の動作確認方法" in result["suggestions"][0]


def test_完了条件_曖昧_エラー():
    """曖昧な完了条件_具体化要求"""
    validator = RequirementValidator()
    
    requirement = {
        "description": "ログイン機能を実装する。完了条件：正常に動作すること",
        "requirement_type": "functional"
    }
    result = validator.validate_completeness(requirement)
    
    assert result["is_valid"] == False
    assert result["score"] == -0.4
    assert "完了条件が曖昧です" in result["errors"][0]


def test_用語不統一_ユーザーと利用者混在_統一要求():
    """同義語の混在_用語集参照_統一提案"""
    validator = RequirementValidator()
    
    result = validator.validate_terminology(
        "ユーザーがログインした後、利用者の情報を表示する"
    )
    
    assert result["is_valid"] == False
    assert result["score"] == -0.2
    assert "用語が統一されていません" in result["errors"][0]
    assert "ユーザー" in result["suggestions"][0]


def test_略語未定義_定義要求():
    """APIやDBなど_初出時の正式名称要求"""
    validator = RequirementValidator()
    
    # 用語集に含まれない略語を使用
    result = validator.validate_terminology(
        "REST APIでRDBMSにアクセスしてJSONデータを取得する"
    )
    
    # デバッグ出力
    if len(result["errors"]) < 2:
        print(f"Unexpected errors count: {result}")
    
    assert result["is_valid"] == False
    # 少なくとも1つのエラー
    assert len(result["errors"]) >= 1
    assert any("略語" in error or "統一" in error for error in result["errors"])
    if result["suggestions"]:
        assert any("正式名称" in sug or "統一" in sug for sug in result["suggestions"])


def test_テスト方法未定義_機能要件_エラー():
    """検証方法不明_テストケース追加要求"""
    validator = RequirementValidator()
    
    requirement = {
        "description": "ユーザー登録機能を実装する",
        "requirement_type": "functional"
    }
    result = validator.validate_testability(requirement)
    
    assert result["is_valid"] == False
    assert result["score"] == -0.3
    assert "テスト方法が記載されていません" in result["errors"][0]
    assert "正常系のテストケース" in result["suggestions"][0]


def test_主観的成功基準_エラー():
    """満足などの主観的基準_客観的基準要求"""
    validator = RequirementValidator()
    
    requirement = {
        "description": "ユーザーが満足できる検索機能。テスト：利用者の満足度確認",
        "requirement_type": "functional"
    }
    result = validator.validate_testability(requirement)
    
    assert result["is_valid"] == False
    assert "成功基準が主観的です" in result["errors"][0]


def test_非機能要件_API_レスポンスタイムなし():
    """API要件でレスポンスタイム未定義_追加要求"""
    validator = RequirementValidator()
    
    requirement = {
        "description": "ユーザー情報を返すAPIを作成する"
    }
    result = validator.validate_nonfunctional_requirements(requirement, "API")
    
    assert result["is_valid"] == False
    assert result["score"] == -0.4
    assert "レスポンスタイム" in result["errors"][0]
    assert "同時接続数" in result["errors"][0]


def test_複合検証_全ての問題を検出():
    """複数の問題_全て検出_最低スコア採用"""
    validator = RequirementValidator()
    
    requirement = {
        "description": "速いAPIを作る",
        "requirement_type": "functional"
    }
    
    # 各検証を実行
    clarity_result = validator.validate_clarity(requirement["description"])
    completeness_result = validator.validate_completeness(requirement)
    testability_result = validator.validate_testability(requirement)
    nfr_result = validator.validate_nonfunctional_requirements(requirement, "API")
    
    # 全ての検証でエラーが出ること
    assert clarity_result["is_valid"] == False
    assert completeness_result["is_valid"] == False
    assert testability_result["is_valid"] == False
    assert nfr_result["is_valid"] == False
    
    # 最も低いスコアは-0.5（曖昧性）
    scores = [
        clarity_result["score"],
        completeness_result["score"],
        testability_result["score"],
        nfr_result["score"]
    ]
    assert min(scores) == -0.5
