"""Architecture analyzer that integrates VSS and AST similarity analysis."""

from pathlib import Path
from typing import Dict, Any, List, Optional, TypedDict, Union


class ArchitectureIssue(TypedDict):
    """An architecture health issue."""
    severity: str  # "high", "medium", "low"
    type: str  # "duplication", "inconsistency", "coupling"
    description: str
    affected_files: List[str]


class ArchitectureMetrics(TypedDict):
    """Metrics for architecture analysis."""
    vss_score: Optional[float]
    ast_score: Optional[float]
    duplication_ratio: float
    consistency_score: float
    coupling_index: float


class ArchitectureHealth(TypedDict):
    """Overall architecture health assessment."""
    score: float
    issues: List[ArchitectureIssue]
    metrics: ArchitectureMetrics


class ArchitectureAnalysisResult(TypedDict):
    """Result of architecture analysis."""
    architecture_health: ArchitectureHealth


def analyze_architecture(
    flake_path: str,
    query: str,
    flakes: List[Dict[str, str]],
    db_path: str,
    language: str = "python"
) -> ArchitectureAnalysisResult:
    """Analyze architecture health by integrating VSS and AST similarity.
    
    Args:
        flake_path: Path to the flake directory to analyze
        query: Query string for VSS search
        flakes: List of flake documents for VSS indexing
        db_path: Path to VSS database
        language: Programming language for AST analysis
    
    Returns:
        Architecture analysis result with health score and issues
    """
    from .vss_adapter import search_similar_flakes
    from .similarity_adapter import detect_code_similarity
    
    issues: List[ArchitectureIssue] = []
    metrics = ArchitectureMetrics(
        vss_score=None,
        ast_score=None,
        duplication_ratio=0.0,
        consistency_score=1.0,
        coupling_index=0.0
    )
    
    # VSS Analysis
    vss_results = None
    try:
        vss_results = search_similar_flakes(query, flakes, db_path, limit=10)
        if vss_results:
            # Calculate VSS score based on similarity scores
            vss_scores = [r["score"] for r in vss_results]
            metrics["vss_score"] = sum(vss_scores) / len(vss_scores) if vss_scores else 0.0
            
            # Detect potential duplications
            high_similarity_threshold = 0.8
            duplicates = [r for r in vss_results if r["score"] > high_similarity_threshold]
            if duplicates:
                issues.append(ArchitectureIssue(
                    severity="high",
                    type="duplication",
                    description=f"Found {len(duplicates)} highly similar components (VSS score > {high_similarity_threshold})",
                    affected_files=[d["id"] for d in duplicates]
                ))
                metrics["duplication_ratio"] = len(duplicates) / len(vss_results)
                
    except Exception as e:
        issues.append(ArchitectureIssue(
            severity="medium",
            type="inconsistency",
            description=f"VSS analysis failed: {str(e)}",
            affected_files=[]
        ))
    
    # AST Analysis
    ast_result = None
    try:
        ast_result = detect_code_similarity(flake_path, language)
        if ast_result and ast_result["ok"]:
            matches = ast_result["matches"]
            if matches:
                # Calculate AST score based on similarity percentages
                ast_scores = [m["similarity"] / 100.0 for m in matches]
                metrics["ast_score"] = sum(ast_scores) / len(ast_scores) if ast_scores else 0.0
                
                # Detect code duplication issues
                high_code_similarity_threshold = 85.0
                code_duplicates = [m for m in matches if m["similarity"] > high_code_similarity_threshold]
                if code_duplicates:
                    for dup in code_duplicates:
                        issues.append(ArchitectureIssue(
                            severity="high",
                            type="duplication",
                            description=f"Code duplication detected: {dup['similarity']:.1f}% similarity\n{dup['details']}",
                            affected_files=[dup["file1"], dup["file2"]]
                        ))
                    
                    # Update duplication ratio with AST findings
                    if metrics["duplication_ratio"] == 0.0:
                        metrics["duplication_ratio"] = len(code_duplicates) / ast_result["total_files"]
                    else:
                        # Average with existing VSS-based ratio
                        metrics["duplication_ratio"] = (
                            metrics["duplication_ratio"] + 
                            len(code_duplicates) / ast_result["total_files"]
                        ) / 2
                        
                # Check for inconsistent patterns
                moderate_similarity_threshold = 50.0
                partial_matches = [m for m in matches if moderate_similarity_threshold < m["similarity"] <= high_code_similarity_threshold]
                if partial_matches:
                    issues.append(ArchitectureIssue(
                        severity="medium",
                        type="inconsistency",
                        description=f"Found {len(partial_matches)} partially similar components that might benefit from refactoring",
                        affected_files=list(set(
                            [m["file1"] for m in partial_matches] +
                            [m["file2"] for m in partial_matches]
                        ))
                    ))
                    metrics["consistency_score"] = 1.0 - (len(partial_matches) / ast_result["total_files"])
                    
        elif ast_result and not ast_result["ok"]:
            issues.append(ArchitectureIssue(
                severity="low",
                type="inconsistency",
                description=f"AST analysis failed: {ast_result['error']}",
                affected_files=[]
            ))
            
    except Exception as e:
        issues.append(ArchitectureIssue(
            severity="low",
            type="inconsistency",
            description=f"AST analysis failed: {str(e)}",
            affected_files=[]
        ))
    
    # Calculate overall health score
    base_score = 1.0
    
    # Deduct for duplication
    base_score -= metrics["duplication_ratio"] * 0.3
    
    # Deduct for inconsistency
    base_score -= (1.0 - metrics["consistency_score"]) * 0.2
    
    # Deduct for high severity issues
    high_severity_count = len([i for i in issues if i["severity"] == "high"])
    base_score -= high_severity_count * 0.1
    
    # Deduct for medium severity issues
    medium_severity_count = len([i for i in issues if i["severity"] == "medium"])
    base_score -= medium_severity_count * 0.05
    
    # Factor in similarity scores if available
    if metrics["vss_score"] is not None and metrics["ast_score"] is not None:
        # High similarity across components might indicate poor separation of concerns
        avg_similarity = (metrics["vss_score"] + metrics["ast_score"]) / 2
        if avg_similarity > 0.7:
            base_score -= (avg_similarity - 0.7) * 0.2
            metrics["coupling_index"] = avg_similarity
    elif metrics["vss_score"] is not None:
        if metrics["vss_score"] > 0.7:
            base_score -= (metrics["vss_score"] - 0.7) * 0.1
            metrics["coupling_index"] = metrics["vss_score"]
    elif metrics["ast_score"] is not None:
        if metrics["ast_score"] > 0.7:
            base_score -= (metrics["ast_score"] - 0.7) * 0.1
            metrics["coupling_index"] = metrics["ast_score"]
    
    # Ensure score is between 0 and 1
    final_score = max(0.0, min(1.0, base_score))
    
    return ArchitectureAnalysisResult(
        architecture_health=ArchitectureHealth(
            score=final_score,
            issues=issues,
            metrics=metrics
        )
    )