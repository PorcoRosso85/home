#!/usr/bin/env python3
import sys
import os

# Add the parent directory (bin/src) to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from requirement.graph.main import main

if __name__ == "__main__":
    main()