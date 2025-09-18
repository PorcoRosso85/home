"""README checker for detecting missing documentation in flake projects"""
from pathlib import Path
from typing import Union, Dict, List
from collections import defaultdict


def check_missing_readmes(root_path: Union[Path, str]) -> list[Path]:
    """
    Check for flake.nix files without corresponding README.md files.
    
    This function recursively searches for all flake.nix files under the given
    root path and checks if a README.md file exists in the same directory.
    It returns a sorted list of directories that contain flake.nix but are
    missing README.md documentation.
    
    Args:
        root_path: Root directory to search for flakes (can be Path or str)
        
    Returns:
        List of directory paths containing flake.nix but missing README.md,
        sorted alphabetically for consistent reporting
        
    Example:
        >>> missing = check_missing_readmes("/home/user/projects")
        >>> for path in missing:
        ...     print(f"Missing README in: {path}")
    """
    # Ensure we have a Path object
    if isinstance(root_path, str):
        root_path = Path(root_path)
        
    missing_readmes = []
    
    # Find all flake.nix files
    for flake_path in root_path.rglob("flake.nix"):
        flake_dir = flake_path.parent
        readme_path = flake_dir / "README.md"
        
        # Check if README.md exists in the same directory
        if not readme_path.exists():
            missing_readmes.append(flake_dir)
    
    # Sort for consistent reporting
    return sorted(missing_readmes, key=str)


def generate_missing_readme_report(root_path: Union[Path, str]) -> str:
    """
    Generate a human-readable report of missing README files with priority grouping.
    
    The report includes:
    - Summary of total missing READMEs
    - Priority-based grouping (src directories are high priority)
    - Relative paths for easy navigation
    
    Args:
        root_path: Root directory to search for flakes
        
    Returns:
        Formatted report as a string
        
    Example:
        >>> report = generate_missing_readme_report("/home/user/projects")
        >>> print(report)
    """
    # Ensure we have a Path object
    if isinstance(root_path, str):
        root_path = Path(root_path)
    
    # Get missing READMEs
    missing_paths = check_missing_readmes(root_path)
    
    if not missing_paths:
        return "🎉 All flake projects have README documentation!"
    
    # Group by priority
    priority_groups: Dict[str, List[Path]] = defaultdict(list)
    
    for path in missing_paths:
        # Determine priority based on path components
        relative_path = path.relative_to(root_path)
        path_parts = relative_path.parts
        
        # Priority rules:
        # - High: src directories or immediate subdirectories
        # - Medium: test, example, or poc directories  
        # - Low: other directories
        if "src" in path_parts[:2]:
            priority = "HIGH"
        elif any(part in ["test", "tests", "example", "examples", "poc"] for part in path_parts):
            priority = "MEDIUM"
        else:
            priority = "LOW"
            
        priority_groups[priority].append(path)
    
    # Build report
    report_lines = [
        "=" * 60,
        "📋 Missing README Alert Report",
        "=" * 60,
        f"\n📊 Summary: {len(missing_paths)} flake(s) missing README documentation\n",
    ]
    
    # Add priority sections
    priority_order = ["HIGH", "MEDIUM", "LOW"]
    priority_labels = {
        "HIGH": "🔴 HIGH Priority (src directories)",
        "MEDIUM": "🟡 MEDIUM Priority (test/example/poc directories)", 
        "LOW": "🟢 LOW Priority (other directories)"
    }
    
    for priority in priority_order:
        if priority not in priority_groups:
            continue
            
        paths = priority_groups[priority]
        report_lines.append(f"\n{priority_labels[priority]} ({len(paths)} missing):")
        report_lines.append("-" * 40)
        
        # Sort paths within priority group
        for path in sorted(paths, key=str):
            relative_path = path.relative_to(root_path)
            report_lines.append(f"  • {relative_path}")
    
    report_lines.extend([
        "\n" + "=" * 60,
        "💡 Recommendation: Start with HIGH priority directories in src/",
        "=" * 60
    ])
    
    return "\n".join(report_lines)