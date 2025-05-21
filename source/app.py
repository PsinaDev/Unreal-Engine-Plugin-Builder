import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDir
from PySide6.QtGui import QIcon

from source.frontend.main_window import MainWindow
from source.frontend.localization import LocalizationManager, LOCALIZATION_CONFIG_FILE
from source.backend.engine_finder import EngineFinder, CONFIG_FILE
from source.frontend import resources_rc

config_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "UnrealPluginBuilder")
os.makedirs(config_dir, exist_ok=True)


def main() -> None:
    """
    Application entry point
    """
    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    app_icon = QIcon(":/icon.ico")
    app.setWindowIcon(app_icon)

    QDir.setSearchPaths("app", [os.path.join(os.path.dirname(__file__), "frontend", "resources")])

    localization = LocalizationManager(config_path=os.path.join(config_dir, LOCALIZATION_CONFIG_FILE))
    finder = EngineFinder(localization, config_path=os.path.join(config_dir, CONFIG_FILE))

    engine_paths = finder.find_all_engines()

    window = MainWindow(engine_paths, localization, finder)
    window.setWindowIcon(app_icon)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
