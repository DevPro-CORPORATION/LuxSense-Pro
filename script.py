"""
LuxSense Pro — Application Entrypoint Wrapper
Routes execution to the software package.
"""

import sys
from software.main import main

if __name__ == "__main__":
    sys.exit(main())
