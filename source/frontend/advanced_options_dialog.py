from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QCheckBox, QComboBox, QLineEdit, QPushButton,
    QDialogButtonBox, QMessageBox, QWidget
)
from typing import Optional, Dict, Any

from source.frontend.localization import LocalizationManager
from source.frontend.manual_engine_dialog import ManualEngineEntryDialog


class AdvancedOptionsDialog(QDialog):
    """
    Dialog with advanced plugin build options
    """

    def __init__(self, parent: Optional[QWidget] = None, localization: Optional[LocalizationManager] = None) -> None:
        super().__init__(parent)
        self.localization = localization
        self.parent_window = parent

        self.setWindowTitle(self.localize("advanced_dialog_title", "Advanced Options"))
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Create language settings group
        layout.addWidget(self.create_language_settings_group())

        # Create build parameters group
        layout.addWidget(self.create_build_parameters_group())

        # Additional buttons
        buttons_layout = QHBoxLayout()

        # Engine rescan button
        self.rescan_engines_button = QPushButton(self.localize("rescan_engines_button", "Rescan Engines"))
        self.rescan_engines_button.clicked.connect(self.rescan_engines)


        # Add Engine button
        self.add_engine_button = QPushButton(self.localize("add_engine_button", "Add Unreal Engine..."))
        self.add_engine_button.clicked.connect(self.add_unreal_engine)

        buttons_layout.addWidget(self.rescan_engines_button)
        buttons_layout.addWidget(self.add_engine_button)

        layout.addLayout(buttons_layout)

        # Standard buttons
        standard_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        standard_buttons.accepted.connect(self.accept)
        standard_buttons.rejected.connect(self.reject)
        layout.addWidget(standard_buttons)

    def localize(self, key: str, default: Optional[str] = None) -> str:
        """
        Get localized text
        """
        if self.localization:
            return self.localization(key, default)
        return default

    def create_language_settings_group(self) -> QGroupBox:
        """
        Create language settings group
        """
        language_group = QGroupBox(self.localize("language_settings", "Language Settings"))

        language_layout = QFormLayout(language_group)
        language_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        language_label = QLabel(self.localize("language_label", "Interface Language:"))
        self.language_combo = QComboBox()
        self.language_combo.addItem(self.localize("language_en", "English"), "en")
        self.language_combo.addItem(self.localize("language_ru", "Русский"), "ru")

        # Set current language
        if self.localization:
            current_lang = self.localization.current_language
            index = self.language_combo.findData(current_lang)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)

        self.apply_language_button = QPushButton(self.localize("apply_language", "Apply"))
        self.apply_language_button.clicked.connect(self.apply_language)

        language_layout.addRow(language_label, self.language_combo)
        language_layout.addRow("", self.apply_language_button)

        return language_group

    def create_build_parameters_group(self) -> QGroupBox:
        """
        Create build parameters group
        """
        params_group = QGroupBox(self.localize("build_parameters_group", "Build Parameters"))

        params_layout = QVBoxLayout(params_group)

        # Platforms - only supported for plugins
        platforms_label = QLabel(self.localize("platforms_label", "Target Platforms:"))
        self.platforms_container = QWidget()
        platforms_layout = QVBoxLayout(self.platforms_container)
        platforms_layout.setContentsMargins(0, 0, 0, 0)

        # Create checkboxes only for platforms relevant to plugins
        self.platform_checkboxes = {}
        for platform in ["Win64", "Win32", "Mac", "Linux"]:
            checkbox = QCheckBox(platform)
            if platform == "Win64":  # Default Win64 selected
                checkbox.setChecked(True)
            platforms_layout.addWidget(checkbox)
            self.platform_checkboxes[platform] = checkbox

        # Compilation options
        options_label = QLabel(self.localize("options_label", "Build Options:"))
        self.options_container = QWidget()
        options_layout = QVBoxLayout(self.options_container)
        options_layout.setContentsMargins(0, 0, 0, 0)

        # Create checkboxes for options
        self.create_dist_checkbox = QCheckBox(
            self.localize("create_dist_checkbox", "CreateSubFolder (create subfolder with build date)"))
        self.no_host_platform_checkbox = QCheckBox(
            self.localize("no_host_platform_checkbox", "NoHostPlatform (do not build for host platform)"))
        self.include_debug_files_checkbox = QCheckBox(
            self.localize("include_debug_files_checkbox", "IncludeDebugFiles (include debug files)"))
        self.strict_checkbox = QCheckBox(
            self.localize("strict_checkbox", "Strict (strict compilation)"))
        self.unversioned_checkbox = QCheckBox(
            self.localize("unversioned_checkbox", "Unversioned (do not embed engine version in descriptor)"))

        options_layout.addWidget(self.create_dist_checkbox)
        options_layout.addWidget(self.no_host_platform_checkbox)
        options_layout.addWidget(self.include_debug_files_checkbox)
        options_layout.addWidget(self.strict_checkbox)
        options_layout.addWidget(self.unversioned_checkbox)

        # Additional parameters (string)
        self.extra_params_label = QLabel(self.localize("extra_params_label", "Additional command line parameters:"))
        self.extra_params_edit = QLineEdit()
        self.extra_params_edit.setPlaceholderText(self.localize("extra_params_placeholder", "-Param1=Value1 -Param2=Value2"))

        # Add all to layout
        form_layout = QFormLayout()
        form_layout.addRow(platforms_label, self.platforms_container)
        form_layout.addRow(options_label, self.options_container)
        form_layout.addRow(self.extra_params_label, self.extra_params_edit)

        params_layout.addLayout(form_layout)

        return params_group

    def apply_language(self) -> None:
        """
        Apply selected language
        """
        if self.localization:
            current_index = self.language_combo.currentIndex()
            lang_code = self.language_combo.itemData(current_index)
            if lang_code and lang_code != self.localization.current_language:
                self.localization.set_language(lang_code)
                QMessageBox.information(
                    self,
                    "Information",
                    "Language changed. Please restart the application for full effect.")

    def add_unreal_engine(self) -> None:
        """
        Manually add Unreal Engine installation
        """
        # Pass existing engines to the dialog
        dialog = ManualEngineEntryDialog(
            self,
            self.localization,
            self.parent_window.engine_finder,
            existing_engines=self.parent_window.engine_paths
        )

        if dialog.exec():
            engines = dialog.get_engines()
            if engines:
                # Save to configuration
                self.parent_window.engine_finder.save_config(engines)
                # Update engine lists in main window
                self.parent_window.update_engines_list(engines)
                # Show confirmation
                QMessageBox.information(
                    self,
                    self.localize("engines_added_title", "Engines Modified"),
                    self.localize("engines_added_message",
                                  f"Unreal Engine installations have been updated.")
                )

    def rescan_engines(self) -> None:
        """
        Rescan available Unreal Engines, forcing a complete scan
        regardless of configuration file
        """
        if hasattr(self.parent_window, "find_engines_forced"):
            self.parent_window.find_engines_forced()
            QMessageBox.information(
                self,
                self.localize("rescan_title", "Scanning Engines"),
                self.localize("rescan_message", "Unreal Engine scanning started."))
        elif hasattr(self.parent_window, "find_engines"):
            # Fallback to regular find_engines if forced method not available
            self.parent_window.find_engines()
            QMessageBox.information(
                self,
                self.localize("rescan_title", "Scanning Engines"),
                self.localize("rescan_message", "Unreal Engine scanning started."))

    def get_build_options(self) -> Dict[str, Any]:
        """
        Get selected build options
        """
        options = {}

        # Add selected platforms
        selected_platforms = []
        for platform, checkbox in self.platform_checkboxes.items():
            if checkbox.isChecked():
                selected_platforms.append(platform)

        if selected_platforms:
            options["TargetPlatforms"] = "+".join(selected_platforms)

        # Add other options
        if self.create_dist_checkbox.isChecked():
            options["CreateSubFolder"] = True

        if self.no_host_platform_checkbox.isChecked():
            options["NoHostPlatform"] = True

        if self.include_debug_files_checkbox.isChecked():
            options["IncludeDebugFiles"] = True

        if self.strict_checkbox.isChecked():
            options["Strict"] = True

        if self.unversioned_checkbox.isChecked():
            options["Unversioned"] = True

        # Add custom parameters
        extra_params = self.extra_params_edit.text().strip()
        if extra_params:
            # Simple parsing of -Param=Value or -Flag
            params = extra_params.split()
            for param in params:
                if param.startswith("-"):
                    param = param[1:]  # Remove leading -
                    if "=" in param:
                        key, value = param.split("=", 1)
                        options[key] = value
                    else:
                        options[param] = True

        return options