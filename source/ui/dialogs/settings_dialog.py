"""
Settings dialog for application preferences.
"""
from typing import Optional, Dict
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QDialogButtonBox,
    QWidget,
    QGroupBox,
    QFileDialog,
    QTabWidget,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QLineEdit,
)
from PySide6.QtCore import Qt

from ..styles import COLORS, FONTS, RADIUS
from .message_dialog import MessageDialog
from ue_plugin_builder.core import (
    tr,
    get_current_language,
    set_language,
    get_available_languages,
    load_custom_locale,
    get_config_manager,
    EngineFinder,
)


class SettingsDialog(QDialog):
    """Dialog for application settings including language and engines."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        engine_finder: Optional[EngineFinder] = None,
        existing_engines: Optional[Dict[str, str]] = None,
    ):
        super().__init__(parent)
        # Create a NEW engine finder without log callback to avoid signal issues
        self._engine_finder = EngineFinder()
        self._engines: Dict[str, str] = dict(existing_engines or {})
        self._config = get_config_manager()
        self._initial_language = get_current_language()
        self._language_changed = False
        
        self.setWindowTitle(tr("settings"))
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
        )
        self.setMinimumWidth(600)
        self.setMinimumHeight(600)
        
        self._setup_ui()
        self._populate_engines()

    def _setup_ui(self) -> None:
        """Set up the UI."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: 8px;
            }}
            QTabWidget::pane {{
                border: 1px solid {COLORS['border_default']};
                border-radius: 6px;
                background-color: {COLORS['bg_primary']};
            }}
            QTabBar::tab {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_muted']};
                padding: 8px 16px;
                border: none;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
            }}
            QTabBar::tab:hover {{
                color: {COLORS['text_secondary']};
            }}
            QListWidget {{
                background-color: {COLORS['bg_primary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 10px 14px;
                border-radius: 6px;
                color: {COLORS['text_primary']};
                margin: 2px 0px;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent_bg']};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['bg_tertiary']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Custom title bar
        title_bar = QHBoxLayout()
        title_bar.setSpacing(8)
        
        title_label = QLabel(tr("settings"))
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 14px;
            font-weight: 600;
        """)
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLORS['text_dim']};
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {COLORS['text_primary']};
            }}
        """)
        close_btn.clicked.connect(self.reject)
        title_bar.addWidget(close_btn)
        
        layout.addLayout(title_bar)

        # Tab widget
        tabs = QTabWidget()
        
        # Engines tab
        engines_tab = self._create_engines_tab()
        tabs.addTab(engines_tab, tr("registered_engines"))
        
        # Language tab
        language_tab = self._create_language_tab()
        tabs.addTab(language_tab, tr("language"))
        
        layout.addWidget(tabs)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("ok"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("cancel"))
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create_engines_tab(self) -> QWidget:
        """Create engines management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Hint label
        hint_label = QLabel(tr("double_click_hint"))
        hint_label.setStyleSheet(f"""
            color: {COLORS['text_dim']};
            font-size: {FONTS['size_xs']};
            font-style: italic;
        """)
        layout.addWidget(hint_label)

        # Engine list
        self._engine_list = QListWidget()
        self._engine_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._engine_list.itemSelectionChanged.connect(self._on_engine_selection_changed)
        self._engine_list.itemDoubleClicked.connect(self._on_engine_double_clicked)
        layout.addWidget(self._engine_list)

        # List buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._remove_btn = QPushButton(tr("remove_selected"))
        self._remove_btn.setEnabled(False)
        self._remove_btn.clicked.connect(self._remove_selected_engines)
        btn_row.addWidget(self._remove_btn)

        btn_row.addStretch()

        scan_btn = QPushButton(tr("scan_for_engines"))
        scan_btn.clicked.connect(self._scan_engines)
        btn_row.addWidget(scan_btn)

        layout.addLayout(btn_row)
        
        # Manual engine adding section
        add_group = QGroupBox(tr("add_engine_manually"))
        add_layout = QVBoxLayout(add_group)
        add_layout.setSpacing(8)
        
        # Path input row
        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText(tr("path_to_ue_installation"))
        self._path_edit.textChanged.connect(self._validate_engine_path)
        path_row.addWidget(self._path_edit)
        
        browse_btn = QPushButton(tr("browse"))
        browse_btn.clicked.connect(self._browse_engine_path)
        path_row.addWidget(browse_btn)
        
        add_layout.addLayout(path_row)
        
        # Version and add row
        version_row = QHBoxLayout()
        version_row.setSpacing(8)
        
        version_label = QLabel(tr("version") + ":")
        version_row.addWidget(version_label)
        
        self._version_edit = QLineEdit()
        self._version_edit.setPlaceholderText(tr("auto_detect"))
        self._version_edit.setMaximumWidth(100)
        version_row.addWidget(self._version_edit)
        
        version_row.addStretch()
        
        self._add_engine_btn = QPushButton(tr("add_engine"))
        self._add_engine_btn.setEnabled(False)
        self._add_engine_btn.setProperty("class", "primary")
        self._add_engine_btn.clicked.connect(self._add_engine_manually)
        version_row.addWidget(self._add_engine_btn)
        
        add_layout.addLayout(version_row)
        
        # Status label
        self._engine_status_label = QLabel("")
        self._engine_status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        add_layout.addWidget(self._engine_status_label)
        
        layout.addWidget(add_group)

        return widget

    def _create_language_tab(self) -> QWidget:
        """Create language settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # Language selection
        lang_group = QGroupBox(tr("select_language"))
        lang_layout = QVBoxLayout(lang_group)

        self._lang_combo = QComboBox()
        for code, name in get_available_languages().items():
            self._lang_combo.addItem(name, code)
        
        current_lang = get_current_language()
        idx = self._lang_combo.findData(current_lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        
        self._lang_combo.currentIndexChanged.connect(self._on_language_selection_changed)
        lang_layout.addWidget(self._lang_combo)

        # Note about restart
        note_label = QLabel(tr("language_restart_note"))
        note_label.setStyleSheet(f"""
            color: {COLORS['text_dim']};
            font-size: {FONTS['size_xs']};
            font-style: italic;
        """)
        lang_layout.addWidget(note_label)

        layout.addWidget(lang_group)

        # Custom locale
        custom_group = QGroupBox(tr("load_custom_locale"))
        custom_layout = QHBoxLayout(custom_group)

        self._locale_path_label = QLabel(tr("no_custom_locale"))
        self._locale_path_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        custom_layout.addWidget(self._locale_path_label, 1)

        load_btn = QPushButton(tr("browse"))
        load_btn.clicked.connect(self._load_custom_locale)
        custom_layout.addWidget(load_btn)

        layout.addWidget(custom_group)
        layout.addStretch()

        return widget

    def _populate_engines(self) -> None:
        """Populate the engine list."""
        self._engine_list.clear()
        
        for version in sorted(self._engines.keys(), reverse=True):
            path = self._engines[version]
            item = QListWidgetItem(f"UE {version}  —  {path}")
            item.setData(Qt.UserRole, version)
            item.setData(Qt.UserRole + 1, path)
            self._engine_list.addItem(item)

    def _on_engine_selection_changed(self) -> None:
        """Handle engine selection change."""
        has_selection = bool(self._engine_list.selectedItems())
        self._remove_btn.setEnabled(has_selection)

    def _on_engine_double_clicked(self, item: QListWidgetItem) -> None:
        """Open engine folder on double click."""
        import os
        import sys
        import subprocess
        
        path = item.data(Qt.UserRole + 1)
        if path and Path(path).exists():
            try:
                if sys.platform == "win32":
                    os.startfile(str(path))
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(path)], check=True)
                else:
                    subprocess.run(["xdg-open", str(path)], check=True)
            except Exception as e:
                MessageDialog.error(self, tr("error"), f"{tr('could_not_open_folder')}:\n{e}")

    def _remove_selected_engines(self) -> None:
        """Remove selected engines."""
        selected = self._engine_list.selectedItems()
        if not selected:
            return

        count = len(selected)
        if count == 1:
            version = selected[0].data(Qt.UserRole)
            message = tr("remove_engine_confirm", version=version)
        else:
            message = f"Remove {count} selected engines from the list?"
        
        result = MessageDialog.question(
            self, tr("remove"), message,
            [tr("no"), tr("yes")]
        )
        
        if result == tr("yes"):
            for item in selected:
                version = item.data(Qt.UserRole)
                if version in self._engines:
                    del self._engines[version]
            self._populate_engines()

    def _scan_engines(self) -> None:
        """Scan for engines."""
        found = self._engine_finder.find_all_engines(force_rescan=True)
        
        if found:
            for version, info in found.items():
                self._engines[version] = str(info.path)
            self._populate_engines()
            message = tr("found_engines", count=len(found)) + "\n\n" + tr("found_engines_hint")
            MessageDialog.information(
                self, tr("scan_for_engines"),
                message
            )
        else:
            MessageDialog.information(
                self, tr("scan_for_engines"),
                tr("no_engines_found")
            )
    
    def _browse_engine_path(self) -> None:
        """Browse for engine directory."""
        path = QFileDialog.getExistingDirectory(
            self,
            tr("select_ue_installation"),
            str(Path.home()),
        )
        if path:
            self._path_edit.setText(path)
    
    def _validate_engine_path(self) -> None:
        """Validate the entered engine path."""
        path_str = self._path_edit.text().strip()
        
        if not path_str:
            self._add_engine_btn.setEnabled(False)
            self._engine_status_label.setText("")
            self._version_edit.setText("")
            return
        
        path = Path(path_str)
        
        if not path.exists():
            self._add_engine_btn.setEnabled(False)
            self._engine_status_label.setText(tr("path_not_exist"))
            self._engine_status_label.setStyleSheet(f"color: {COLORS['error']};")
            self._version_edit.setText("")
            return
        
        if not self._engine_finder.is_valid_engine_path(path):
            self._add_engine_btn.setEnabled(False)
            self._engine_status_label.setText(tr("not_valid_engine"))
            self._engine_status_label.setStyleSheet(f"color: {COLORS['error']};")
            self._version_edit.setText("")
            return
        
        # Try to detect version
        version = self._engine_finder.extract_version(path)
        if version:
            self._version_edit.setText(version)
            self._engine_status_label.setText(f"{tr('detected_ue')} {version}")
            self._engine_status_label.setStyleSheet(f"color: {COLORS['success']};")
        else:
            self._version_edit.setText("")
            self._engine_status_label.setText(tr("valid_engine_unknown_version"))
            self._engine_status_label.setStyleSheet(f"color: {COLORS['warning']};")
        
        self._add_engine_btn.setEnabled(True)
    
    def _add_engine_manually(self) -> None:
        """Add engine manually."""
        path_str = self._path_edit.text().strip()
        version = self._version_edit.text().strip()
        
        if not path_str:
            return
        
        if not version:
            MessageDialog.warning(
                self, tr("version"),
                tr("version_required")
            )
            return
        
        # Check for duplicate
        if version in self._engines:
            result = MessageDialog.question(
                self, tr("version"),
                tr("version_exists", version=version),
                [tr("no"), tr("yes")]
            )
            if result != tr("yes"):
                return
        
        self._engines[version] = path_str
        self._populate_engines()
        
        # Clear inputs
        self._path_edit.clear()
        self._version_edit.clear()
        self._engine_status_label.setText(tr("engine_added"))
        self._engine_status_label.setStyleSheet(f"color: {COLORS['success']};")

    def _on_language_selection_changed(self, index: int) -> None:
        """Handle language selection change."""
        new_lang = self._lang_combo.currentData()
        if new_lang != self._initial_language:
            self._language_changed = True

    def _load_custom_locale(self) -> None:
        """Load custom locale file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("load_custom_locale"),
            str(Path.home()),
            "JSON Files (*.json)"
        )
        
        if file_path:
            if load_custom_locale(Path(file_path)):
                self._locale_path_label.setText(Path(file_path).name)
                MessageDialog.information(
                    self, tr("language"),
                    tr("locale_loaded")
                )
            else:
                MessageDialog.error(
                    self, tr("error"),
                    tr("locale_load_error")
                )

    def _on_accept(self) -> None:
        """Handle dialog accept - save settings."""
        # Save language
        new_lang = self._lang_combo.currentData()
        set_language(new_lang)
        self._config.update_config(language=new_lang)
        
        # Show restart message if language changed
        if self._language_changed:
            MessageDialog.information(
                self, tr("language"),
                tr("restart_to_apply")
            )
        
        self.accept()

    def get_engines(self) -> Dict[str, str]:
        """Get configured engines."""
        return self._engines.copy()
