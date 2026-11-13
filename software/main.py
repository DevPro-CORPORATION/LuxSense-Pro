"""
LuxSense Pro — Application Entrypoint
Launches the PySide6 Qt WebEngine desktop application with React + TypeScript frontend.
"""

import sys
from software.core.webengine_host import run_desktop_app

def main():
    return run_desktop_app()

if __name__ == "__main__":
    sys.exit(main())

