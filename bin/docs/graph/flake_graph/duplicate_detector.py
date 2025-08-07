"""Duplicate flake detection functionality."""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import tempfile

from flake_graph.vss_adapter import search_similar_flakes, create_flake_document


def detect_language(text: str) -> str:
    """
    Detect if text is primarily Japanese, English, or mixed.
    
    Args:
        text: Text content to analyze
        
    Returns:
        One of: 'japanese', 'english', 'mixed', 'unknown'
    """
    if not text or not text.strip():
        return 'unknown'
    
    # Remove whitespace and normalize
    text = text.strip()
    
    # Count character types
    japanese_chars = len(re.findall(r'[ひらがなカタカナ一-龯]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    total_chars = len(re.sub(r'\s', '', text))  # Exclude whitespace from total
    
    if total_chars == 0:
        return 'unknown'
    
    japanese_ratio = japanese_chars / total_chars
    english_ratio = english_chars / total_chars
    
    # Thresholds for language detection
    if japanese_ratio > 0.3:
        if english_ratio > 0.2:
            return 'mixed'
        else:
            return 'japanese'
    elif english_ratio > 0.5:
        return 'english'
    else:
        # Check for mixed content with lower thresholds
        if japanese_ratio > 0.1 and english_ratio > 0.1:
            return 'mixed'
        elif japanese_ratio > english_ratio:
            return 'japanese'
        elif english_ratio > japanese_ratio:
            return 'english'
        else:
            return 'unknown'


def detect_cross_language_duplicates(
    flakes: List[Dict[str, Any]],
    similarity_threshold: float = 0.7,
    min_cross_lang_score: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Detect cross-language duplicates between Japanese and English flakes.
    
    This function identifies flakes that are likely translations or similar content
    expressed in different languages (Japanese vs English).
    
    Args:
        flakes: List of flake information dictionaries
        similarity_threshold: Standard similarity threshold for VSS matching
        min_cross_lang_score: Minimum similarity score for cross-language matches
        
    Returns:
        List of cross-language duplicate groups, each containing:
        - description: Representative description
        - language_pair: Languages involved (e.g., "japanese-english")
        - flakes: List of flakes in the group
        - similarity_score: Average cross-language similarity score
        - mixed_language_flakes: List of flakes with mixed language content
    """
    if not flakes:
        return []
    
    # Classify flakes by language
    japanese_flakes = []
    english_flakes = []
    mixed_flakes = []
    
    for flake in flakes:
        description = flake.get("description", "")
        readme_content = flake.get("readme_content", "")
        combined_content = f"{description} {readme_content}".strip()
        
        language = detect_language(combined_content)
        flake_with_lang = {**flake, "detected_language": language, "combined_content": combined_content}
        
        if language == 'japanese':
            japanese_flakes.append(flake_with_lang)
        elif language == 'english':
            english_flakes.append(flake_with_lang)
        elif language == 'mixed':
            mixed_flakes.append(flake_with_lang)
    
    if not japanese_flakes or not english_flakes:
        # Need both languages for cross-language detection
        return []
    
    cross_language_groups = []
    
    # Use VSS to find cross-language similarities
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "cross_language_detection.kuzu"
        
        # Import vss_kuzu and create VSS instance
        from vss_kuzu import create_vss
        vss = create_vss(db_path=str(db_path))
        
        # Handle VSS initialization failure
        if isinstance(vss, dict) and 'type' in vss:
            return []
        
        # Create documents for all flakes
        all_categorized_flakes = japanese_flakes + english_flakes + mixed_flakes
        documents = []
        flake_map = {}
        
        # Extract base_path if available
        base_path = None
        if all_categorized_flakes and isinstance(all_categorized_flakes[0].get("path"), Path):
            all_paths = [f["path"] for f in all_categorized_flakes if isinstance(f.get("path"), Path)]
            if all_paths:
                try:
                    base_path = Path(os.path.commonpath([str(p) for p in all_paths]))
                    if base_path.name == "flake.nix":
                        base_path = base_path.parent
                except ValueError:
                    base_path = None
        
        for i, flake in enumerate(all_categorized_flakes):
            doc = create_flake_document(flake, base_path=base_path)
            doc["id"] = f"flake_{i}"
            doc["language"] = flake["detected_language"]
            documents.append(doc)
            flake_map[doc["id"]] = flake
        
        # Index all documents
        vss.index(documents)
        
        # Find cross-language pairs
        processed_pairs = set()
        
        # Compare Japanese flakes against English flakes
        for jp_doc in [d for d in documents if flake_map[d["id"]]["detected_language"] == 'japanese']:
            search_result = vss.search(jp_doc["content"], limit=len(documents))
            
            if isinstance(search_result, dict) and "results" in search_result:
                for result in search_result["results"]:
                    result_flake = flake_map[result["id"]]
                    
                    # Only consider English or mixed language results
                    if result_flake["detected_language"] in ['english', 'mixed'] and result["score"] >= min_cross_lang_score:
                        # Avoid duplicate pairs
                        pair_key = tuple(sorted([jp_doc["id"], result["id"]]))
                        if pair_key not in processed_pairs:
                            processed_pairs.add(pair_key)
                            
                            # Create cross-language group
                            jp_flake = flake_map[jp_doc["id"]]
                            en_flake = result_flake
                            
                            # Determine language pair type
                            if en_flake["detected_language"] == 'mixed':
                                lang_pair = "japanese-mixed"
                            else:
                                lang_pair = "japanese-english"
                            
                            group_flakes = [jp_flake, en_flake]
                            mixed_lang_flakes = [f for f in group_flakes if f["detected_language"] == 'mixed']
                            
                            cross_language_groups.append({
                                "description": jp_flake.get("description", en_flake.get("description", "")),
                                "language_pair": lang_pair,
                                "flakes": group_flakes,
                                "similarity_score": result["score"],
                                "mixed_language_flakes": mixed_lang_flakes
                            })
        
        # Also check mixed-language flakes against both Japanese and English
        for mixed_doc in [d for d in documents if flake_map[d["id"]]["detected_language"] == 'mixed']:
            search_result = vss.search(mixed_doc["content"], limit=len(documents))
            
            if isinstance(search_result, dict) and "results" in search_result:
                best_match = None
                best_score = 0.0
                
                for result in search_result["results"]:
                    result_flake = flake_map[result["id"]]
                    
                    # Consider Japanese or English matches
                    if (result_flake["detected_language"] in ['japanese', 'english'] and 
                        result["score"] >= min_cross_lang_score and 
                        result["score"] > best_score):
                        
                        pair_key = tuple(sorted([mixed_doc["id"], result["id"]]))
                        if pair_key not in processed_pairs:
                            best_match = result
                            best_score = result["score"]
                
                if best_match:
                    processed_pairs.add(tuple(sorted([mixed_doc["id"], best_match["id"]])))
                    
                    mixed_flake = flake_map[mixed_doc["id"]]
                    match_flake = flake_map[best_match["id"]]
                    
                    lang_pair = f"mixed-{match_flake['detected_language']}"
                    
                    cross_language_groups.append({
                        "description": mixed_flake.get("description", match_flake.get("description", "")),
                        "language_pair": lang_pair,
                        "flakes": [mixed_flake, match_flake],
                        "similarity_score": best_score,
                        "mixed_language_flakes": [mixed_flake]
                    })
    
    return cross_language_groups


def find_duplicate_flakes(
    flakes: List[Dict[str, Any]], 
    use_vss: bool = False,
    similarity_threshold: float = 0.8,
    include_cross_language: bool = False
) -> List[Dict[str, Any]]:
    """
    Find duplicate or similar flakes based on their descriptions.
    
    Args:
        flakes: List of flake information dictionaries
        use_vss: Whether to use VSS for similarity detection
        similarity_threshold: Minimum similarity score for VSS matching
        include_cross_language: Whether to include cross-language duplicates
    
    Returns:
        List of duplicate groups, each containing:
        - description: The duplicate description
        - flakes: List of flakes with this description
        - similarity_score: (VSS only) Average similarity score
        - language_pair: (Cross-language only) Language pair information
        - mixed_language_flakes: (Cross-language only) Flakes with mixed languages
    """
    if use_vss:
        duplicates = _find_similar_flakes_with_vss(flakes, similarity_threshold)
        
        if include_cross_language:
            # Add cross-language duplicates
            cross_lang_duplicates = detect_cross_language_duplicates(
                flakes, 
                similarity_threshold=similarity_threshold,
                min_cross_lang_score=max(0.6, similarity_threshold - 0.1)
            )
            duplicates.extend(cross_lang_duplicates)
        
        return duplicates
    else:
        return _find_exact_duplicates(flakes)


def _find_exact_duplicates(flakes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find flakes with exactly matching descriptions."""
    # Group flakes by description
    description_groups: Dict[str, List[Dict[str, Any]]] = {}
    
    for flake in flakes:
        desc = flake.get("description", "")
        if desc:
            if desc not in description_groups:
                description_groups[desc] = []
            description_groups[desc].append(flake)
    
    # Find duplicates (groups with more than one flake)
    duplicates = []
    for description, flake_list in description_groups.items():
        if len(flake_list) > 1:
            duplicates.append({
                "description": description,
                "flakes": flake_list
            })
    
    return duplicates


def _find_similar_flakes_with_vss(
    flakes: List[Dict[str, Any]], 
    similarity_threshold: float
) -> List[Dict[str, Any]]:
    """Find similar flakes using VSS with complete-linkage clustering."""
    if not flakes:
        return []
    
    # Create temporary database for VSS
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "duplicate_detection.kuzu"
        
        # Convert flakes to VSS documents
        documents = []
        flake_map = {}  # Map document ID to original flake
        
        # Extract base_path if all flakes share a common base
        base_path = None
        if flakes and isinstance(flakes[0].get("path"), Path):
            # Try to find common base path
            all_paths = [f["path"] for f in flakes if isinstance(f.get("path"), Path)]
            if all_paths:
                # Find common parent
                try:
                    base_path = Path(os.path.commonpath([str(p) for p in all_paths]))
                    if base_path.name == "flake.nix":
                        base_path = base_path.parent
                except ValueError:
                    # No common path, use None
                    base_path = None
        
        for i, flake in enumerate(flakes):
            # Create document using the adapter function for consistency
            doc = create_flake_document(flake, base_path=base_path)
            # Override ID to maintain mapping
            doc["id"] = f"flake_{i}"
            documents.append(doc)
            flake_map[doc["id"]] = flake
        
        # Import vss_kuzu and create a single VSS instance
        from vss_kuzu import create_vss
        vss = create_vss(db_path=str(db_path))
        
        # Handle VSS initialization failure
        if isinstance(vss, dict) and 'type' in vss:
            # VSS initialization failed, return empty list
            return []
        
        # Index all documents once
        vss.index(documents)
        
        # Build pairwise similarity matrix
        similarity_matrix = {}
        
        # Compute all pairwise similarities
        for i, doc in enumerate(documents):
            # Search for similar documents using the same VSS instance
            search_result = vss.search(doc["content"], limit=len(documents))
            
            # Handle search results
            if isinstance(search_result, dict) and "results" in search_result:
                for result in search_result["results"]:
                    if result["id"] != doc["id"]:  # Skip self-similarity
                        pair = tuple(sorted([doc["id"], result["id"]]))
                        if pair not in similarity_matrix:
                            similarity_matrix[pair] = result["score"]
        
        
        # Build groups using complete-linkage clustering
        similar_groups = []
        processed_ids = set()
        
        for doc in documents:
            if doc["id"] in processed_ids:
                continue
            
            # Start a new group with current document
            current_group = {doc["id"]}
            processed_ids.add(doc["id"])
            
            # Try to add documents that are similar to ALL in current group
            changed = True
            while changed:
                changed = False
                for other_doc in documents:
                    if other_doc["id"] in current_group or other_doc["id"] in processed_ids:
                        continue
                    
                    # Check if this document is similar to ALL documents in current group
                    min_similarity = 1.0
                    for member_id in current_group:
                        pair = tuple(sorted([member_id, other_doc["id"]]))
                        similarity = similarity_matrix.get(pair, 0.0)
                        min_similarity = min(min_similarity, similarity)
                    
                    # Add only if similar to all members
                    if min_similarity >= similarity_threshold:
                        current_group.add(other_doc["id"])
                        processed_ids.add(other_doc["id"])
                        changed = True
            
            # Add group if it has more than one flake
            if len(current_group) > 1:
                group_flakes = [flake_map[doc_id] for doc_id in current_group]
                
                # Calculate average similarity within group
                total_similarity = 0.0
                pair_count = 0
                group_list = list(current_group)
                for i in range(len(group_list)):
                    for j in range(i + 1, len(group_list)):
                        pair = tuple(sorted([group_list[i], group_list[j]]))
                        total_similarity += similarity_matrix.get(pair, 0.0)
                        pair_count += 1
                
                similar_groups.append({
                    "description": group_flakes[0]["description"],
                    "flakes": group_flakes,
                    "similarity_score": total_similarity / pair_count if pair_count > 0 else 0.0
                })
        
        return similar_groups


def detect_and_report_duplicates(
    base_dir: Path,
    flakes: List[Dict[str, Any]],
    use_vss: bool = False,
    similarity_threshold: float = 0.8,
    include_cross_language: bool = False
) -> str:
    """
    Detect and generate a report of duplicate flakes.
    
    Args:
        base_dir: Base directory for relative paths
        flakes: List of flake information
        use_vss: Whether to use VSS for similarity detection
        similarity_threshold: Minimum similarity score for VSS matching
        include_cross_language: Whether to include cross-language duplicates
    
    Returns:
        Formatted report string
    """
    duplicates = find_duplicate_flakes(
        flakes, 
        use_vss=use_vss, 
        similarity_threshold=similarity_threshold,
        include_cross_language=include_cross_language
    )
    
    if not duplicates:
        return "No duplicate flakes found."
    
    # Separate regular duplicates from cross-language duplicates
    regular_duplicates = [d for d in duplicates if "language_pair" not in d]
    cross_lang_duplicates = [d for d in duplicates if "language_pair" in d]
    
    report_lines = []
    
    if regular_duplicates:
        report_lines.append(f"Found {len(regular_duplicates)} duplicate group(s):")
        
        for i, dup_group in enumerate(regular_duplicates, 1):
            report_lines.append(f"\n{i}. Description: {dup_group['description']}")
            
            if "similarity_score" in dup_group:
                report_lines.append(f"   Similarity Score: {dup_group['similarity_score']:.2f}")
            
            report_lines.append("   Flakes:")
            for flake in dup_group["flakes"]:
                rel_path = flake["path"].relative_to(base_dir) if isinstance(flake["path"], Path) else flake["path"]
                report_lines.append(f"   - {rel_path}")
    
    if cross_lang_duplicates:
        if report_lines:
            report_lines.append("")  # Add separator
        
        report_lines.append(f"Found {len(cross_lang_duplicates)} cross-language duplicate group(s):")
        
        for i, dup_group in enumerate(cross_lang_duplicates, 1):
            report_lines.append(f"\n{i}. Cross-Language Pair ({dup_group['language_pair']})")
            report_lines.append(f"   Description: {dup_group['description']}")
            report_lines.append(f"   Similarity Score: {dup_group['similarity_score']:.2f}")
            
            if dup_group.get("mixed_language_flakes"):
                report_lines.append(f"   Mixed-Language Flakes: {len(dup_group['mixed_language_flakes'])}")
            
            report_lines.append("   Flakes:")
            for flake in dup_group["flakes"]:
                rel_path = flake["path"].relative_to(base_dir) if isinstance(flake["path"], Path) else flake["path"]
                lang_info = f" [{flake.get('detected_language', 'unknown')}]"
                report_lines.append(f"   - {rel_path}{lang_info}")
    
    if not report_lines:
        return "No duplicate flakes found."
    
    return "\n".join(report_lines)