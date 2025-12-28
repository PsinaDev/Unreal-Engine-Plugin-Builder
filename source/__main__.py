"""
Entry point for running UE Plugin Builder as a module.

Usage:
    python -m ue_plugin_builder           # Launch GUI
    python -m ue_plugin_builder --help    # Show help
"""

import sys
from .app import main


if __name__ == "__main__":
    sys.exit(main())
