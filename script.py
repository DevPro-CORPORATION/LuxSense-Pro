"""
LuxSense Pro — Legacy Entrypoint Wrapper
Preserves backward compatibility while loading the modular application architecture.
"""

import sys
from app.main import main

if __name__ == "__main__":
    sys.exit(main())
