"""
UE Plugin Builder - Main Application

This module provides the entry point for the GUI application.
Can be packaged as standalone .exe using PyInstaller:

    pyinstaller --onefile --windowed --name "UE Plugin Builder" app.py
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

# Fix imports for direct execution (IDE, PyInstaller, python app.py)
if __name__ == "__main__" or getattr(sys, "frozen", False):
    # Add parent directory to path so we can import ue_plugin_builder
    _app_dir = Path(__file__).parent.resolve()
    _parent_dir = _app_dir.parent
    if str(_parent_dir) not in sys.path:
        sys.path.insert(0, str(_parent_dir))

# Configure logging before any other imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def setup_high_dpi() -> None:
    """Enable high DPI scaling for Qt application."""
    # Only set if not already configured by user
    # Don't force scaling - let Qt handle it naturally
    pass


def get_application_path() -> Path:
    """Get the application base path (works for both dev and frozen exe)."""
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        return Path(sys.executable).parent
    else:
        # Running as script
        return Path(__file__).parent


def _import_core():
    """Import core modules with fallback for direct execution."""
    try:
        from ue_plugin_builder.core import get_config_manager, set_language, detect_system_language
        return get_config_manager, set_language, detect_system_language
    except ImportError:
        from .core import get_config_manager, set_language, detect_system_language
        return get_config_manager, set_language, detect_system_language


def _import_ui():
    """Import UI modules with fallback for direct execution."""
    try:
        from ue_plugin_builder.ui import MainWindow
        return MainWindow
    except ImportError:
        from .ui import MainWindow
        return MainWindow


def _import_version():
    """Import version with fallback for direct execution."""
    try:
        from ue_plugin_builder import __version__
        return __version__
    except ImportError:
        from . import __version__
        return __version__


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for UE Plugin Builder GUI.
    
    Args:
        argv: Command line arguments (uses sys.argv if None)
    
    Returns:
        Exit code (0 for success)
    """
    if argv is None:
        argv = sys.argv[1:]
    
    # Handle --help before Qt imports
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        print("\nUsage: ue_plugin_builder [options]")
        print("\nOptions:")
        print("  -h, --help     Show this help message")
        print("  --version      Show version information")
        print("\nTo use programmatically:")
        print("  from ue_plugin_builder import PluginBuilder, BuildConfig")
        return 0
    
    if "--version" in argv:
        __version__ = _import_version()
        print(f"UE Plugin Builder v{__version__}")
        return 0
    
    # Setup high DPI before importing Qt
    setup_high_dpi()
    
    # Initialize localization - load from config or detect system
    get_config_manager, set_language, detect_system_language = _import_core()
    config_manager = get_config_manager()
    config = config_manager.load_config()
    
    # Use saved language or detect from system
    if config.language:
        set_language(config.language)
    else:
        detected_lang = detect_system_language()
        set_language(detected_lang)
        config_manager.update_config(language=detected_lang)
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        
        MainWindow = _import_ui()
    except ImportError as e:
        logger.error(f"Failed to import Qt: {e}")
        print("Error: PySide6 is required for the GUI.")
        print("Install it with: pip install PySide6")
        return 1
    
    # Create application
    app = QApplication([sys.argv[0]] + list(argv))
    app.setApplicationName("UE Plugin Builder")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("UEAutomation")
    
    # Set default font
    font = QFont()
    if sys.platform == "win32":
        font.setFamily("Segoe UI")
    elif sys.platform == "darwin":
        font.setFamily("SF Pro")
    else:
        font.setFamily("Ubuntu")
    font.setPointSize(10)
    app.setFont(font)
    
    # Create and show main window
    try:
        window = MainWindow()
        window.show()
        
        logger.info("Application started")
        return app.exec()
        
    except Exception as e:
        logger.exception(f"Application error: {e}")
        
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "Application Error",
            f"An unexpected error occurred:\n\n{e}\n\nPlease check the logs for details."
        )
        return 1


def run_headless(
    plugin_path: str,
    output_path: str,
    engine_path: str,
    **options
) -> int:
    """
    Run plugin build in headless mode (no GUI).
    
    Args:
        plugin_path: Path to .uplugin file
        output_path: Output directory
        engine_path: Path to UE engine
        **options: Additional build options
    
    Returns:
        Exit code (0 for success)
    """
    try:
        from ue_plugin_builder import PluginBuilder, BuildConfig, BuildStatus
    except ImportError:
        from . import PluginBuilder, BuildConfig, BuildStatus
    
    def log_handler(msg):
        print(f"[{msg.level.name}] {msg.text}")
    
    builder = PluginBuilder(log_callback=log_handler)
    
    config = BuildConfig(
        plugin_path=Path(plugin_path),
        output_path=Path(output_path),
        engine_path=Path(engine_path),
        **options
    )
    
    result = builder.build_plugin(config, blocking=True)
    
    if result.status == BuildStatus.SUCCESS:
        print(f"\n✓ Build successful: {result.output_path}")
        return 0
    else:
        print(f"\n✗ Build failed: {result.message}")
        for error in result.errors[:10]:
            print(f"  - {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
