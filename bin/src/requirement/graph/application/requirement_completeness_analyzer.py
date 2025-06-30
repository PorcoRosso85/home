"""
RequirementCompletenessAnalyzer - 要件完全性分析
依存: なし
外部依存: なし

プロジェクト全体の要件カバレッジと重複を分析
"""
from typing import List, Dict, Any, TypedDict, Set
import re


class CompletenessAnalysis(TypedDict):
    """完全性分析結果"""
    is_complete: bool
    missing_categories: List[str]
    coverage: Dict[str, float]
    duplicates: List[Dict[str, Any]]
    recommendations: List[Dict[str, str]]


class RequirementCompletenessAnalyzer:
    """要件の完全性と網羅性を分析"""
    
    def __init__(self):
        # 必須カテゴリの定義
        self.required_categories = {
            "security",
            "performance",
            "functional",
            "usability",
            "reliability"
        }
        
        # カテゴリ識別キーワード
        self.category_keywords = {
            "security": ["セキュリティ", "認証", "認可", "暗号", "security", "auth", "encryption"],
            "performance": ["パフォーマンス", "性能", "レスポンス", "performance", "response", "throughput"],
            "functional": ["機能", "feature", "functional", "ユーザー管理", "データ処理"],
            "usability": ["使いやすさ", "ユーザビリティ", "UI", "UX", "usability", "interface"],
            "reliability": ["信頼性", "可用性", "エラー", "リカバリ", "reliability", "availability"]
        }
    
    def analyze_completeness(self, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        要件セットの完全性を分析
        
        Args:
            requirements: 要件のリスト
            
        Returns:
            完全性分析結果
            
        Example:
            >>> analyzer = RequirementCompletenessAnalyzer()
            >>> reqs = [
            ...     {"ID": "req1", "Title": "User Management", "Tags": ["feature", "user"]},
            ...     {"ID": "req2", "Title": "API Performance", "Tags": ["performance", "api"]}
            ... ]
            >>> analysis = analyzer.analyze_completeness(reqs)
            >>> "security" in analysis["missing_categories"]
            True
        """
        # カテゴリ別カバレッジを計算
        category_coverage = self._calculate_category_coverage(requirements)
        
        # 欠落カテゴリを特定
        missing_categories = [
            cat for cat in self.required_categories
            if category_coverage.get(cat, 0) == 0
        ]
        
        # 重複要件を検出
        duplicates = self._detect_duplicates(requirements)
        
        # 推奨事項を生成
        recommendations = self._generate_recommendations(
            missing_categories,
            category_coverage,
            duplicates
        )
        
        # 完全性判定
        is_complete = len(missing_categories) == 0 and len(duplicates) == 0
        
        return {
            "is_complete": is_complete,
            "missing_categories": missing_categories,
            "coverage": category_coverage,
            "duplicates": duplicates,
            "recommendations": recommendations
        }
    
    def _calculate_category_coverage(self, requirements: List[Dict[str, Any]]) -> Dict[str, float]:
        """カテゴリ別のカバレッジを計算"""
        category_counts = {cat: 0 for cat in self.required_categories}
        
        for req in requirements:
            categories = self._identify_categories(req)
            for cat in categories:
                if cat in category_counts:
                    category_counts[cat] += 1
        
        # パーセンテージに変換（0-100）
        total_reqs = len(requirements) if requirements else 1
        coverage = {}
        
        for cat, count in category_counts.items():
            # 各カテゴリに少なくとも1つの要件があれば100%、なければ0%
            coverage[cat] = 100.0 if count > 0 else 0.0
        
        return coverage
    
    def _identify_categories(self, requirement: Dict[str, Any]) -> Set[str]:
        """要件が属するカテゴリを識別"""
        categories = set()
        
        # タグから識別
        tags = requirement.get("Tags", [])
        for tag in tags:
            tag_lower = tag.lower()
            for cat, keywords in self.category_keywords.items():
                if any(kw.lower() in tag_lower for kw in keywords):
                    categories.add(cat)
        
        # タイトルと説明から識別
        title = requirement.get("Title", "").lower()
        description = requirement.get("Description", "").lower()
        text = f"{title} {description}"
        
        for cat, keywords in self.category_keywords.items():
            if any(kw.lower() in text for kw in keywords):
                categories.add(cat)
        
        return categories
    
    def _detect_duplicates(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重複または類似した要件を検出"""
        duplicates = []
        
        # 簡易的な重複検出：タイトルやMetadataの類似性をチェック
        for i, req1 in enumerate(requirements):
            for j, req2 in enumerate(requirements[i + 1:], start=i + 1):
                similarity = self._calculate_similarity(req1, req2)
                
                if similarity > 0.8:  # 80%以上の類似度
                    duplicates.append({
                        "requirement_ids": [req1["ID"], req2["ID"]],
                        "similarity_score": similarity
                    })
        
        return duplicates
    
    def _calculate_similarity(self, req1: Dict[str, Any], req2: Dict[str, Any]) -> float:
        """2つの要件の類似度を計算（0.0-1.0）"""
        # Metadataの比較
        meta1 = req1.get("Metadata", {})
        meta2 = req2.get("Metadata", {})
        
        # 同じtechnologyとpurposeを持つ場合は高い類似度
        if (meta1.get("technology") == meta2.get("technology") and
            meta1.get("purpose") == meta2.get("purpose") and
            meta1.get("technology") is not None):
            return 0.9
        
        # タグの比較
        tags1 = set(req1.get("Tags", []))
        tags2 = set(req2.get("Tags", []))
        
        if tags1 and tags2:
            intersection = len(tags1 & tags2)
            union = len(tags1 | tags2)
            if union > 0:
                return intersection / union
        
        return 0.0
    
    def _generate_recommendations(
        self,
        missing_categories: List[str],
        coverage: Dict[str, float],
        duplicates: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """改善推奨事項を生成"""
        recommendations = []
        
        # 欠落カテゴリに対する推奨
        for cat in missing_categories:
            recommendations.append({
                "category": cat,
                "recommendation": f"{cat}要件が不足しています。追加を検討してください。"
            })
        
        # 低カバレッジカテゴリに対する推奨
        for cat, cov in coverage.items():
            if 0 < cov < 50 and cat not in missing_categories:
                recommendations.append({
                    "category": cat,
                    "recommendation": f"{cat}要件のカバレッジが低い({cov:.0f}%)です。"
                })
        
        # 重複に対する推奨
        if duplicates:
            recommendations.append({
                "category": "duplication",
                "recommendation": f"{len(duplicates)}件の重複要件が検出されました。統合を検討してください。"
            })
        
        return recommendations


# In-source tests
def test_completeness_analyzer_missing_security():
    """セキュリティ要件の欠落を検出"""
    analyzer = RequirementCompletenessAnalyzer()
    
    requirements = [
        {
            "ID": "feat_user_001",
            "Title": "User Management Feature",
            "Description": "User registration and profile management",
            "Tags": ["feature", "user"]
        },
        {
            "ID": "perf_api_001",
            "Title": "API Performance Requirements",
            "Description": "API response time requirements",
            "Tags": ["performance", "api"]
        }
    ]
    
    analysis = analyzer.analyze_completeness(requirements)
    
    assert analysis["is_complete"] is False
    assert "security" in analysis["missing_categories"]
    assert analysis["coverage"]["security"] == 0
    assert len([r for r in analysis["recommendations"] if r["category"] == "security"]) > 0


def test_completeness_analyzer_detect_duplicates():
    """重複要件を検出"""
    analyzer = RequirementCompletenessAnalyzer()
    
    requirements = [
        {
            "ID": "cache_req_001",
            "Title": "Implement Caching Layer",
            "Tags": ["cache", "redis", "performance"],
            "Metadata": {"technology": "redis", "purpose": "api_cache"}
        },
        {
            "ID": "cache_req_002",
            "Title": "API Response Caching",
            "Tags": ["performance", "cache", "redis"],
            "Metadata": {"technology": "redis", "purpose": "api_cache"}
        }
    ]
    
    analysis = analyzer.analyze_completeness(requirements)
    
    assert len(analysis["duplicates"]) == 1
    assert set(analysis["duplicates"][0]["requirement_ids"]) == {"cache_req_001", "cache_req_002"}
    assert analysis["duplicates"][0]["similarity_score"] > 0.8


def test_completeness_analyzer_complete_set():
    """完全な要件セットの場合"""
    analyzer = RequirementCompletenessAnalyzer()
    
    requirements = [
        {"ID": "sec_001", "Title": "Authentication System", "Tags": ["security", "auth"]},
        {"ID": "perf_001", "Title": "Performance Monitoring", "Tags": ["performance"]},
        {"ID": "func_001", "Title": "User Management", "Tags": ["functional", "feature"]},
        {"ID": "ui_001", "Title": "User Interface Design", "Tags": ["usability", "UI"]},
        {"ID": "rel_001", "Title": "Error Recovery", "Tags": ["reliability", "error"]}
    ]
    
    analysis = analyzer.analyze_completeness(requirements)
    
    assert analysis["is_complete"] is True
    assert len(analysis["missing_categories"]) == 0
    assert all(cov > 0 for cov in analysis["coverage"].values())