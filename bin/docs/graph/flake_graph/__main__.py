"""Enable running as python -m flake_graph."""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())