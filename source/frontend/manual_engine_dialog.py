from typing import Dict, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QFormLayout, QLineEdit, QWidget
)
from PySide6.QtCore import Qt

from source.backend.engine_finder import EngineFinder
from source.frontend.localization import LocalizationManager


class ManualEngineEntryDialog(QDialog):
    """
    Dialog for manually adding Unreal Engine installations
    """

    def __init__(self, parent: Optional[QWidget] = None,
                 localization: Optional[LocalizationManager] = None,
                 engine_finder: Optional[EngineFinder] = None,
                 existing_engines: Optional[Dict[str, str]] = None) -> None:

        super().__init__(parent)
        self.localization = localization
        self.engine_finder = engine_finder

        # Initialize with existing engines if provided
        self.engines_list = existing_engines.copy() if existing_engines else {}

        self.setWindowTitle(self.localize("manual_engines_title", "Add Unreal Engine Installations"))
        self.setMinimumSize(600, 400)

        self.init_ui()

        self.populate_engines_list()

    def localize(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        """Get localized text"""
        if self.localization:
            return self.localization(key, default, **kwargs)
        return default if default is not None else key

    def populate_engines_list(self) -> None:
        """Populate the list widget with existing engines"""
        for version, path in self.engines_list.items():
            item_text = f"{version} - {path}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, version)  # Store version as item data
            self.list_widget.addItem(item)

        # Enable save button if we have engines
        self.save_button.setEnabled(len(self.engines_list) > 0)

    def init_ui(self) -> None:
        """Initialize user interface"""
        layout = QVBoxLayout(self)

        # Instructions - different text based on whether we have existing engines
        if self.engines_list:
            instructions = QLabel(self.localize(
                "manual_engines_edit_instructions",
                "Manage your Unreal Engine installations below.\n"
                "You can add new installations or remove existing ones."
            ))
        else:
            instructions = QLabel(self.localize(
                "manual_engines_instructions",
                "Automatic search didn't find any Unreal Engine installations.\n"
                "Please add your Unreal Engine installations manually."
            ))

        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self.list_widget)

        # Form for adding new engine
        form_group = QFormLayout()

        # Version input
        version_layout = QHBoxLayout()
        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText(self.localize("engine_version_placeholder", "e.g. 5.1"))
        version_layout.addWidget(self.version_edit)

        # Path input and browse button
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(self.localize("engine_path_placeholder", "Path to Unreal Engine"))

        browse_button = QPushButton("...")
        browse_button.setFixedWidth(40)
        browse_button.clicked.connect(self.browse_engine_path)

        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_button)

        form_group.addRow(self.localize("engine_version_label", "Engine Version:"), version_layout)
        form_group.addRow(self.localize("engine_path_label", "Engine Path:"), path_layout)

        layout.addLayout(form_group)

        # Buttons for list management
        buttons_layout = QHBoxLayout()

        self.add_button = QPushButton(self.localize("add_engine_button", "Add Engine"))
        self.add_button.clicked.connect(self.add_engine)

        self.remove_button = QPushButton(self.localize("remove_engine_button", "Remove Selected"))
        self.remove_button.clicked.connect(self.remove_engine)
        self.remove_button.setEnabled(False)

        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.remove_button)
        layout.addLayout(buttons_layout)

        # Connect list selection change
        self.list_widget.itemSelectionChanged.connect(self.selection_changed)

        # Dialog buttons
        dialog_buttons = QHBoxLayout()
        self.save_button = QPushButton(self.localize("save_engines_button", "Save and Continue"))
        self.save_button.clicked.connect(self.accept)

        cancel_button = QPushButton(self.localize("cancel_button", "Cancel"))
        cancel_button.clicked.connect(self.reject)

        dialog_buttons.addStretch()
        dialog_buttons.addWidget(cancel_button)
        dialog_buttons.addWidget(self.save_button)
        layout.addLayout(dialog_buttons)

    def browse_engine_path(self) -> None:
        """Open file dialog to select Unreal Engine directory"""
        folder = QFileDialog.getExistingDirectory(
            self,
            self.localize("select_engine_folder", "Select Unreal Engine Directory")
        )

        if folder:
            self.path_edit.setText(folder)

            # Try to auto-detect version from folder
            if not self.version_edit.text():
                if self.engine_finder:
                    version = self.engine_finder.extract_version_from_path(folder)
                    if version:
                        self.version_edit.setText(version)

    def add_engine(self) -> None:
        """Add engine to the list"""
        version = self.version_edit.text().strip()
        path = self.path_edit.text().strip()

        if not version:
            QMessageBox.warning(
                self,
                self.localize("error_title", "Error"),
                self.localize("error_no_version", "Please enter an engine version.")
            )
            return

        if not path:
            QMessageBox.warning(
                self,
                self.localize("error_title", "Error"),
                self.localize("error_no_path", "Please select an engine path.")
            )
            return

        # Validate engine path
        if self.engine_finder and not self.engine_finder.is_valid_engine_path(path):
            result = QMessageBox.question(
                self,
                self.localize("invalid_engine_title", "Invalid Engine Path"),
                self.localize("invalid_engine_message",
                              "This doesn't appear to be a valid Unreal Engine installation.\n"
                              "Do you want to add it anyway?"),
                QMessageBox.Yes | QMessageBox.No
            )
            if result != QMessageBox.Yes:
                return

        # Add to our dictionary and list widget
        self.engines_list[version] = path
        item_text = f"{version} - {path}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, version)  # Store version as item data
        self.list_widget.addItem(item)

        # Clear form
        self.version_edit.clear()
        self.path_edit.clear()

        # Enable save button if we have engines
        self.save_button.setEnabled(len(self.engines_list) > 0)

    def remove_engine(self) -> None:
        """Remove selected engine from the list"""
        current_item = self.list_widget.currentItem()
        if current_item:
            version = current_item.data(Qt.UserRole)
            if version in self.engines_list:
                del self.engines_list[version]

            self.list_widget.takeItem(self.list_widget.row(current_item))

            # Disable save button if no engines left
            self.save_button.setEnabled(len(self.engines_list) > 0)

    def selection_changed(self) -> None:
        """Update button state based on selection"""
        self.remove_button.setEnabled(self.list_widget.currentItem() is not None)

    def get_engines(self) -> Dict[str, str]:
        """Return the entered engines dictionary"""
        return self.engines_list