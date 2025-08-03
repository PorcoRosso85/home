#!/usr/bin/env python3
"""Demo script to show missing README alert report functionality"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from flake_graph.readme_checker import generate_missing_readme_report

def main():
    # Example: Check current project's parent directories
    # In real usage, you'd point this to your project root
    root_path = Path("/home/nixos/bin")
    
    print("Generating Missing README Alert Report...")
    print("Root directory:", root_path)
    print()
    
    # Generate the report
    report = generate_missing_readme_report(root_path)
    
    # Display the report
    print(report)
    
    # You can also save this to a file
    # with open("missing_readme_report.txt", "w") as f:
    #     f.write(report)

if __name__ == "__main__":
    main()