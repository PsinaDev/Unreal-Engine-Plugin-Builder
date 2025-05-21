import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QPushButton, QRadioButton,
    QGroupBox, QFrame, QFileDialog, QDialog, QDialogButtonBox,
    QMessageBox, QApplication, QSizePolicy
)
from PySide6.QtGui import QColor, QIcon, QDragEnterEvent, QDropEvent, QPainter, QPen, QBrush
from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import QEvent, QProcess, Qt
from PySide6.QtGui import QPalette
from typing import Optional, Dict

from source.backend.engine_finder import EngineFinder
from source.frontend.console_widget import ConsoleWidget
from source.frontend.advanced_options_dialog import AdvancedOptionsDialog
from source.backend.plugin_builder import PluginBuilder
from source.frontend.localization import LocalizationManager
from source.frontend.manual_engine_dialog import ManualEngineEntryDialog


class PluginDragDropSupport:
    """
    Mixin to add drag and drop support to the plugin group box
    """

    def __init__(self, widget, plugin_path_edit, update_callback):
        self.target_widget = widget
        self.plugin_path_edit = plugin_path_edit
        self.update_callback = update_callback
        self.isDragging = False
        self.isValidDrag = False

        # Create an overlay widget for the X
        from PySide6.QtWidgets import QWidget
        self.overlay = QWidget(self.target_widget)
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.overlay.setStyleSheet("background-color: transparent;")
        self.overlay.hide()

        # Create custom paint method for overlay
        def paintOverlay(event):
            if not self.isValidDrag:
                painter = QPainter(self.overlay)
                painter.setRenderHint(QPainter.Antialiasing)

                # Draw X
                painter.setPen(QPen(QColor("#F44336"), 3))
                size = min(50, min(self.overlay.width(), self.overlay.height()) / 4)
                x = (self.overlay.width() - size) / 2
                y = (self.overlay.height() - size) / 2
                painter.drawLine(x, y, x + size, y + size)
                painter.drawLine(x + size, y, x, y + size)

        # Assign custom paint method to overlay
        self.overlay.paintEvent = paintOverlay

        # Install event filter
        self.target_widget.setAcceptDrops(True)
        self.target_widget.dragEnterEvent = self.dragEnterEvent
        self.target_widget.dragLeaveEvent = self.dragLeaveEvent
        self.target_widget.dragMoveEvent = self.dragMoveEvent
        self.target_widget.dropEvent = self.dropEvent
        self.target_widget.paintEvent_original = self.target_widget.paintEvent
        self.target_widget.paintEvent = self.paintEvent

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event"""
        # Check if the drag has URLs (files/folders)
        if event.mimeData().hasUrls():
            # Get the first URL
            url = event.mimeData().urls()[0]
            path = url.toLocalFile()

            # Check if it's a directory
            if os.path.isdir(path):
                # Check if directory contains a .uplugin file
                try:
                    uplugin_files = [f for f in os.listdir(path) if f.endswith('.uplugin')]
                    if uplugin_files:
                        self.isValidDrag = True
                        event.acceptProposedAction()
                    else:
                        # Directory doesn't contain uplugin file
                        self.isValidDrag = False
                        event.acceptProposedAction()  # Still accept to show feedback
                except (PermissionError, FileNotFoundError):
                    self.isValidDrag = False
            elif path.endswith('.uplugin'):
                # Direct uplugin file
                self.isValidDrag = True
                event.acceptProposedAction()
            else:
                self.isValidDrag = False

        self.isDragging = True

        # Resize and show overlay
        self.overlay.resize(self.target_widget.size())
        self.overlay.show()
        self.overlay.raise_()  # Ensure it's on top

        self.target_widget.update()
        self.overlay.update()

    def dragLeaveEvent(self, event) -> None:
        """Handle drag leave event"""
        self.isDragging = False
        self.overlay.hide()
        self.target_widget.update()

    def dragMoveEvent(self, event) -> None:
        """Handle drag move event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event"""
        self.isDragging = False
        self.overlay.hide()

        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            path = url.toLocalFile()

            if os.path.isdir(path):
                # Find .uplugin file in directory
                try:
                    uplugin_files = [f for f in os.listdir(path) if f.endswith('.uplugin')]
                    if uplugin_files:
                        # Use the first .uplugin file found
                        plugin_path = os.path.join(path, uplugin_files[0])
                        self.plugin_path_edit.setText(plugin_path)
                        if self.update_callback:
                            self.update_callback()
                except (PermissionError, FileNotFoundError):
                    pass
            elif path.endswith('.uplugin'):
                # Direct .uplugin file
                self.plugin_path_edit.setText(path)
                if self.update_callback:
                    self.update_callback()

        self.target_widget.update()

    def paintEvent(self, event) -> None:
        """Custom paint event to show drag state"""
        # Call the original paint event first
        self.target_widget.paintEvent_original(event)

        if self.isDragging:
            painter = QPainter(self.target_widget)
            painter.setRenderHint(QPainter.Antialiasing)

            if self.isValidDrag:
                # Valid drop target - show green highlight
                painter.setPen(QPen(QColor("#4CAF50"), 2))
                painter.setBrush(QBrush(QColor(76, 175, 80, 40)))
            else:
                # Invalid drop target - show red background
                painter.setPen(QPen(QColor("#F44336"), 2))
                painter.setBrush(QBrush(QColor(244, 67, 54, 40)))

            # Draw filled rectangle with border
            painter.drawRect(2, 2, self.target_widget.width() - 4, self.target_widget.height() - 4)


class MainWindow(QMainWindow):
    """
    Main window of the UE Plugin Builder application
    """

    def __init__(self, engine_paths: Optional[Dict[str, str]] = None,
                 localization: Optional[LocalizationManager] = None,
                 finder: Optional[EngineFinder] = None) -> None:

        super().__init__()

        # Initialize variables
        self.engine_paths = engine_paths or {}
        self.localization = localization
        self.plugin_builder = PluginBuilder(localization)
        self.engine_finder = finder
        self.advanced_options = {}

        # Set up backend signals
        self.plugin_builder.signals.log_message.connect(self.handle_log_message)
        self.plugin_builder.signals.build_started.connect(self.handle_build_started)
        self.plugin_builder.signals.build_finished.connect(self.handle_build_finished)

        self.engine_finder.signals.log_message.connect(self.handle_log_message)

        # Initialize UI
        self.init_ui()

        # If no engines were found, start search
        if not self.engine_paths:
            self.find_engines()

    def localize(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        """
        Get localized text
        """
        if self.localization:
            return self.localization(key, default, **kwargs)
        return default if default is not None else key

    def init_ui(self) -> None:
        """
        Initialize user interface
        """

        self.setWindowTitle(self.localize("main_window_title", "UE Plugin Builder"))
        self.setMinimumSize(800, 600)

        # Apply dark theme
        self.apply_dark_theme()

        # Central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(7, 7, 7, 7)
        main_layout.setSpacing(7)

        # Top section with settings - fixed height to prevent vertical stretching
        top_panel = QWidget()
        top_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Only expand horizontally
        settings_layout = QHBoxLayout(top_panel)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(7)

        # === LEFT COLUMN: Plugin ===
        plugin_group = QGroupBox(self.localize("plugin_group", "Plugin"))
        plugin_group.setStyleSheet(self.get_group_style())
        plugin_layout = QVBoxLayout(plugin_group)
        plugin_layout.setContentsMargins(5, 15, 5, 5)
        plugin_layout.setSpacing(5)

        # Plugin selection
        plugin_file_layout = QHBoxLayout()
        plugin_label = QLabel(self.localize("plugin_file_label", "Select .uplugin file:"))
        self.plugin_path_edit = QLineEdit()
        self.plugin_path_edit.setPlaceholderText(self.localize("plugin_path_placeholder", "Path to plugin file..."))
        self.plugin_path_edit.textChanged.connect(self.update_plugin_info)

        plugin_file_button = QPushButton("...")
        plugin_file_button.setFixedWidth(30)
        plugin_file_button.clicked.connect(self.browse_plugin)

        plugin_file_layout.addWidget(plugin_label)
        plugin_file_layout.addWidget(self.plugin_path_edit, 1)
        plugin_file_layout.addWidget(plugin_file_button)

        # Add a small hint label for drag & drop
        drag_drop_hint = QLabel(self.localize("drop_hint", "Or drag & drop plugin folder here"))
        drag_drop_hint.setStyleSheet("color: #8A8A8A; font-style: italic; font-size: 8pt;")

        # Plugin information - SEPARATE LABEL from content (as in Image 2)
        plugin_info_label = QLabel(self.localize("plugin_info_label", "Plugin Information:"))

        # Plugin info text as a separate widget with its own background
        self.plugin_info_text = QLabel(self.localize("plugin_info_empty", "No information. Please select a plugin..."))
        self.plugin_info_text.setStyleSheet("background-color: #383838; padding: 5px; border-radius: 4px;")
        self.plugin_info_text.setWordWrap(True)
        self.plugin_info_text.setTextFormat(Qt.RichText)
        self.plugin_info_text.setMinimumHeight(80)  # Ensure there's enough vertical space

        # Add warning label for version match at the bottom of plugin info section
        self.version_match_warning = QLabel(
            self.localize("version_match_warning", "Warning: Target version matches plugin version!"))
        self.version_match_warning.setStyleSheet("color: #FF5252; font-weight: bold; margin-top: 3px;")
        self.version_match_warning.setAlignment(Qt.AlignCenter)
        self.version_match_warning.hide()  # Initially hidden

        plugin_layout.addLayout(plugin_file_layout)
        plugin_layout.addWidget(drag_drop_hint)
        plugin_layout.addWidget(plugin_info_label)
        plugin_layout.addWidget(self.plugin_info_text)
        plugin_layout.addWidget(self.version_match_warning)

        # Enable drag & drop for the plugin group
        self.plugin_drag_drop = PluginDragDropSupport(
            plugin_group,
            self.plugin_path_edit,
            self.update_plugin_info
        )

        # === RIGHT COLUMN: Unreal Engine + Output Directory ===
        right_column = QVBoxLayout()
        right_column.setSpacing(7)  # Spacing between the two sections

        # Create Unreal Engine section
        engine_group = QGroupBox(self.localize("engine_group", "Unreal Engine"))
        engine_group.setStyleSheet(self.get_group_style())
        engine_layout = QVBoxLayout(engine_group)
        engine_layout.setContentsMargins(5, 15, 5, 5)
        engine_layout.setSpacing(5)
        engine_layout.setAlignment(Qt.AlignTop)  # Align to top to prevent stretching

        # Target UE version - fixed positioning without stretching
        target_layout = QHBoxLayout()
        target_layout.setAlignment(Qt.AlignLeft)  # Align left to prevent stretching

        self.target_version_label = QLabel(self.localize("target_version_label", "Target UE Version:"))
        self.target_version_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Prevent size changes

        self.target_version_combo = QComboBox()
        self.target_version_combo.addItems(self.engine_paths.keys())
        for i in range(self.target_version_combo.count()):
            version_text = self.target_version_combo.itemText(i)
            if version_text in self.engine_paths:
                self.target_version_combo.setItemData(i, self.engine_paths[version_text], Qt.ToolTipRole)
        self.target_version_combo.setMinimumWidth(120)
        self.target_version_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Prevent size changes
        self.target_version_combo.currentIndexChanged.connect(self.check_version_match)

        target_layout.addWidget(self.target_version_label)
        target_layout.addWidget(self.target_version_combo)
        target_layout.addStretch()  # Add stretch at the end, not between widgets

        engine_layout.addLayout(target_layout)

        # Add spacer to prevent stretching
        engine_layout.addStretch()

        # Create Output Directory section
        output_group = QGroupBox(self.localize("output_group", "Output Directory"))
        output_group.setStyleSheet(self.get_group_style())
        output_layout = QVBoxLayout(output_group)
        output_layout.setContentsMargins(5, 15, 5, 5)
        output_layout.setSpacing(5)
        output_layout.setAlignment(Qt.AlignTop)  # Align to top to prevent stretching

        # Radio buttons with fixed positioning
        radio_container = QVBoxLayout()
        radio_container.setAlignment(Qt.AlignLeft)  # Align left to prevent stretching

        self.same_dir_radio = QRadioButton(self.localize("same_dir_radio", "To parent directory"))
        self.same_dir_radio.setToolTip("Plugin will be saved with UE version suffix.\nExample: MyPlugin_UE_X.X")
        self.same_dir_radio.setChecked(True)
        self.same_dir_radio.toggled.connect(self.update_output_path)
        self.same_dir_radio.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Prevent size changes

        self.other_dir_radio = QRadioButton(self.localize("other_dir_radio", "Select another directory"))
        self.other_dir_radio.toggled.connect(self.update_output_path)
        self.other_dir_radio.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Prevent size changes

        radio_container.addWidget(self.same_dir_radio)
        radio_container.addWidget(self.other_dir_radio)

        output_layout.addLayout(radio_container)

        # Output path with fixed positioning
        output_dir_layout = QHBoxLayout()
        output_dir_layout.setAlignment(Qt.AlignLeft)  # Align left to prevent stretching

        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Path...")
        self.output_path_edit.setEnabled(False)
        self.output_path_edit.setMinimumWidth(180)  # Set minimum width

        self.output_dir_button = QPushButton("...")
        self.output_dir_button.setFixedWidth(30)
        self.output_dir_button.setEnabled(False)
        self.output_dir_button.clicked.connect(self.browse_output)

        output_dir_layout.addWidget(self.output_path_edit)
        output_dir_layout.addWidget(self.output_dir_button)

        output_layout.addLayout(output_dir_layout)

        # Add spacer to prevent stretching
        output_layout.addStretch()

        # Add the sections to the right column
        right_column.addWidget(engine_group)
        right_column.addWidget(output_group)
        right_column.addStretch()  # Add stretch at the bottom to prevent sections from stretching vertically

        # Add columns to settings layout
        settings_layout.addWidget(plugin_group, 2)  # Plugin group takes more space
        settings_layout.addLayout(right_column, 1)  # Right column with both sections

        # Console - should expand to fill available space
        console_frame = QFrame()
        console_frame.setFrameShape(QFrame.StyledPanel)
        console_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Expand both ways
        console_frame.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 1px solid #3F3F46;
                border-radius: 3px;
            }
        """)

        console_layout = QVBoxLayout(console_frame)
        console_layout.setContentsMargins(5, 5, 5, 5)

        self.console = ConsoleWidget(localization=self.localization)
        self.console.setMinimumHeight(120)  # Reduced minimum height to allow more flexibility
        self.console.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Make console expand

        console_layout.addWidget(self.console)

        # Bottom panel with buttons
        bottom_panel = QWidget()
        bottom_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Only expand horizontally
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(5)

        # Advanced options button
        self.advanced_button = QPushButton(self.localize("advanced_button", "Advanced Options"))
        self.advanced_button.setIcon(QIcon.fromTheme("preferences-system"))
        self.advanced_button.clicked.connect(self.show_advanced_options)

        # Help button
        self.help_button = QPushButton(self.localize("help_button", "BuildPlugin Help"))
        self.help_button.clicked.connect(self.show_build_plugin_help)

        # Action buttons
        self.clear_console_button = QPushButton(self.localize("clear_console_button", "Clear Console"))
        self.clear_console_button.clicked.connect(self.console.clear_console)

        self.show_command_button = QPushButton(self.localize("show_command_button", "Show Command"))
        self.show_command_button.clicked.connect(self.show_command)

        self.build_button = QPushButton(self.localize("build_button", "Build Plugin"))
        self.build_button.clicked.connect(self.build_plugin)
        self.build_button.setStyleSheet("""
            QPushButton {
                    background-color: #0078D4;
                    color: white;
                    padding: 6px 12px;
                    font-weight: bold;
                    border-radius: 4px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #106EBE;
                }
                QPushButton:pressed {
                    background-color: #005A9E;
                }
        """)

        bottom_layout.addWidget(self.advanced_button)
        bottom_layout.addWidget(self.help_button)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.clear_console_button)
        bottom_layout.addWidget(self.show_command_button)
        bottom_layout.addWidget(self.build_button)

        # Assemble main layout - use fixed height widgets for top and bottom
        main_layout.addWidget(top_panel)
        main_layout.addWidget(console_frame, 1)  # Give stretch factor to console
        main_layout.addWidget(bottom_panel)

        # Set central widget
        self.setCentralWidget(central_widget)

        # Display initial messages in console
        self.console.append_text(self.localize("ready_message", "Ready to rebuild plugin."))
        self.console.append_text(self.localize("select_plugin_message",
                                               "Select plugin and build parameters, then click \"Build Plugin\"."))

        # Connect localization signal
        if self.localization:
            self.localization.language_changed.connect(self.update_ui_language)

    def check_version_match(self) -> None:
        """
        Check if plugin engine version matches target version and show warning if needed
        """
        plugin_path = self.plugin_path_edit.text()
        if not plugin_path or not os.path.exists(plugin_path):
            self.version_match_warning.hide()
            return

        # Get plugin info
        plugin_info = self.plugin_builder.extract_plugin_info(plugin_path)
        if not plugin_info or not plugin_info.get('is_engine_plugin') or not plugin_info.get('engine_version'):
            self.version_match_warning.hide()
            return

        target_version = self.target_version_combo.currentText()

        if plugin_info['engine_version'] in target_version or target_version in plugin_info['engine_version']:
            self.version_match_warning.show()
        else:
            self.version_match_warning.hide()

    def update_ui_language(self) -> None:
        """
        Update UI elements after language change
        """
        # Update window title
        self.setWindowTitle(self.localize("main_window_title", "UE Plugin Builder"))

        # Update group boxes
        for widget in self.findChildren(QGroupBox):
            if widget.objectName() == "engine_group":
                widget.setTitle(self.localize("engine_group", "Unreal Engine"))
            elif widget.objectName() == "plugin_group":
                widget.setTitle(self.localize("plugin_group", "Plugin"))
            elif widget.objectName() == "output_group":
                widget.setTitle(self.localize("output_group", "Output Directory"))

        # Update labels
        self.target_version_label.setText(self.localize("target_version_label", "Target UE Version:"))

        # Update version match warning
        self.version_match_warning.setText(self.localize("version_match_warning",
                                                         "Warning: Target version matches plugin version!"))

        # Update empty plugin info text if no plugin selected
        if self.plugin_path_edit.text() == "":
            self.plugin_info_text.setText(
                self.localize("plugin_info_empty", "No information. Please select a plugin..."))

        # Update radio buttons
        self.same_dir_radio.setText(self.localize("same_dir_radio", "To parent directory with UE version"))
        self.other_dir_radio.setText(self.localize("other_dir_radio", "Select another directory"))

        # Update buttons
        self.advanced_button.setText(self.localize("advanced_button", "Advanced Options"))
        self.help_button.setText(self.localize("help_button", "BuildPlugin Help"))
        self.clear_console_button.setText(self.localize("clear_console_button", "Clear Console"))
        self.show_command_button.setText(self.localize("show_command_button", "Show Command"))
        self.build_button.setText(self.localize("build_button", "Build Plugin"))

    def get_group_style(self) -> str:
        """
        Return style for QGroupBox
        """
        return """
            QGroupBox {
                background-color: #2D2D30;
                border: 1px solid #3F3F46;
                border-radius: 3px;
                margin-top: 1ex; /* Space for the title */
                font-weight: bold;
                padding: 3px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                color: #CCCCCC;
            }
        """

    def apply_dark_theme(self) -> None:
        """
        Apply dark theme to the entire application
        """
        dark_palette = self.palette()

        # Set colors for dark theme
        dark_palette.setColor(QPalette.Window, QColor("#2D2D30"))
        dark_palette.setColor(QPalette.WindowText, QColor("#CCCCCC"))
        dark_palette.setColor(QPalette.Base, QColor("#252526"))
        dark_palette.setColor(QPalette.AlternateBase, QColor("#3F3F41"))
        dark_palette.setColor(QPalette.ToolTipBase, QColor("#2D2D30"))
        dark_palette.setColor(QPalette.ToolTipText, QColor("#CCCCCC"))
        dark_palette.setColor(QPalette.Text, QColor("#CCCCCC"))
        dark_palette.setColor(QPalette.Button, QColor("#2D2D30"))
        dark_palette.setColor(QPalette.ButtonText, QColor("#CCCCCC"))
        dark_palette.setColor(QPalette.BrightText, QColor("#FFFFFF"))
        dark_palette.setColor(QPalette.Link, QColor("#42A5F5"))
        dark_palette.setColor(QPalette.Highlight, QColor("#0078D7"))
        dark_palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))

        # Set palette
        self.setPalette(dark_palette)

    def find_engines(self) -> None:
        """
        Start search for installed Unreal Engines
        """
        self.console.append_text(self.localize("log_engines_search_start", "Starting Unreal Engine search..."), "INFO")

        # Start search in a separate thread
        import threading

        def search_thread():
            engines = self.engine_finder.find_all_engines()
            # Update interface from main thread
            QApplication.instance().postEvent(
                self,
                EnginesFoundEvent(engines)
            )

        threading.Thread(target=search_thread).start()

    def find_engines_forced(self) -> None:
        """
        Start forced search for installed Unreal Engines,
        ignoring any existing configuration
        """
        self.console.append_text("Starting forced Unreal Engine search (ignoring configuration)...", "INFO")

        # Start search in a separate thread
        import threading

        def search_thread_forced():
            engines = self.engine_finder.find_all_engines(force_rescan=True)
            # Update interface from main thread
            QApplication.instance().postEvent(
                self,
                EnginesFoundEvent(engines)
            )

        threading.Thread(target=search_thread_forced).start()

    def update_engines_list(self, engines: Dict[str, str]) -> None:
        """
        Update Unreal Engine version lists
        """
        # If no engines found with automatic detection, show manual entry dialog
        if not engines:
            dialog = ManualEngineEntryDialog(
                self,
                self.localization,
                self.engine_finder,
                existing_engines=self.engine_paths  # Pass existing engines
            )
            if dialog.exec():
                # User added engines manually
                engines = dialog.get_engines()
                # Save to configuration
                self.engine_finder.save_config(engines)
            else:
                # User cancelled - add an empty engine option to allow the application to run
                if not self.engine_paths:  # Only add placeholder if no existing engines
                    self.console.append_text(
                        self.localize("no_engines_warning",
                                      "No Unreal Engine installations added. Please add engines via Advanced Options."),
                        "WARNING"
                    )
                    engines = {"(No engines found)": ""}
                else:
                    # Keep existing engines if user cancels
                    engines = self.engine_paths

        self.engine_paths = engines

        # Clear combo boxes
        self.target_version_combo.clear()

        # Add found versions with tooltips showing engine paths
        for version in sorted(engines.keys(), reverse=True):
            # Use UE_ prefix for display
            display_text = version

            # Add to target combobox with tooltip
            self.target_version_combo.addItem(display_text)
            self.target_version_combo.setItemData(self.target_version_combo.count() - 1, f"{engines[version]}",
                                                  Qt.ToolTipRole)

            # # If more than one version, select next for target
            # if self.target_version_combo.count() > 1:
            #     self.target_version_combo.setCurrentIndex(1)

    def browse_plugin(self) -> None:
        """
        Open file dialog to select plugin file
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.localize("select_uplugin_file", "Select .uplugin file"),
            "",
            "Unreal Plugin (*.uplugin)"
        )

        if file_path:
            self.plugin_path_edit.setText(file_path)
            self.update_plugin_info()
            self.update_output_path()

    def update_plugin_info(self) -> None:
        """
        Update information about selected plugin
        """
        plugin_path = self.plugin_path_edit.text()

        if not plugin_path or not os.path.exists(plugin_path):
            self.plugin_info_text.setText(
                self.localize("plugin_info_empty", "No information. Please select a plugin..."))
            self.version_match_warning.hide()  # Hide warning when no plugin
            return

        plugin_info = self.plugin_builder.extract_plugin_info(plugin_path)

        if plugin_info:
            info_text = (
                f"<b>{self.localize('plugin_info_name', 'Name:')}</b> {plugin_info['name']}<br>"
                f"<b>{self.localize('plugin_info_version', 'Version:')}</b> {plugin_info['version']}<br>"
                f"<b>{self.localize('plugin_info_category', 'Category:')}</b> {plugin_info['category']}<br>"
                f"<b>{self.localize('plugin_info_description', 'Description:')}</b> {plugin_info['description']}<br>"
                f"<b>{self.localize('plugin_info_modules', 'Modules:')}</b> {', '.join(plugin_info['modules'])}<br>"
            )

            if plugin_info['is_engine_plugin']:
                info_text += f"<b>{self.localize('plugin_info_engine_version', 'Engine Version:')}</b> {plugin_info['engine_version']}<br>"

            if plugin_info['marketplace_url']:
                info_text += f"<b>{self.localize('plugin_info_marketplace_url', 'Marketplace URL:')}</b> {plugin_info['marketplace_url']}<br>"

            if plugin_info['supported_platforms']:
                info_text += f"<b>{self.localize('plugin_info_supported_platforms', 'Supported Platforms:')}</b> {', '.join(plugin_info['supported_platforms'])}"

            self.plugin_info_text.setText(info_text)

            self.check_version_match()
        else:
            self.plugin_info_text.setText(self.localize("plugin_info_error", "Error reading plugin information."))
            self.version_match_warning.hide()  # Hide warning on error

    def browse_output(self) -> None:
        """
        Open dialog to select save folder
        """
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.localize("select_output_folder", "Select folder to save plugin")
        )

        if folder_path:
            self.output_path_edit.setText(folder_path)
            # Switch to "Select another directory" option
            self.other_dir_radio.setChecked(True)

    def update_output_path(self) -> None:
        """
        Update output directory selection elements state
        """
        # Enable/disable input fields based on selected option
        self.output_path_edit.setEnabled(self.other_dir_radio.isChecked())
        self.output_dir_button.setEnabled(self.other_dir_radio.isChecked())


    def get_target_engine_path(self) -> Optional[str]:
        """
        Return path to target UE version
        """
        selected_version = self.target_version_combo.currentText()
        # Strip UE_ prefix if present
        if selected_version.startswith("UE_"):
            selected_version = selected_version[3:]
        return self.engine_paths.get(selected_version)

    def get_output_path(self) -> str:
        """
        Return path for saving built plugin
        """
        plugin_path = self.plugin_path_edit.text()

        if not plugin_path:
            return ""

        # Extract plugin name without extension
        plugin_dir = os.path.dirname(plugin_path)
        plugin_name = os.path.splitext(os.path.basename(plugin_path))[0]

        target_version = self.target_version_combo.currentText()

        if self.same_dir_radio.isChecked():
            # Use parent directory instead of current directory
            parent_dir = os.path.dirname(plugin_dir)

            # Get plugin folder name
            plugin_folder_name = os.path.basename(plugin_dir)

            # Extract base plugin name (without version if specified in folder name)
            base_folder_name = plugin_folder_name.split('_')[0]

            # Create new directory name with target version
            new_folder_name = f"{base_folder_name}_{target_version}"

            # Form full path
            output_path = os.path.join(parent_dir, new_folder_name)

            # Check if output path matches input path
            if os.path.normpath(output_path) == os.path.normpath(plugin_dir):
                # If matches, add suffix
                output_path = f"{output_path}_build"
        else:
            # Return user-selected directory with plugin name and version
            custom_dir = self.output_path_edit.text()
            output_path = os.path.join(custom_dir, f"{plugin_name}_{target_version}")

        # Normalize path and replace backslashes with forward slashes
        return os.path.normpath(output_path).replace("\\", "/")

    def show_advanced_options(self) -> None:
        """
        Show dialog with advanced build options
        """
        dialog = AdvancedOptionsDialog(self, self.localization)
        if dialog.exec():
            self.advanced_options = dialog.get_build_options()

    def show_build_plugin_help(self) -> None:
        """
        Show BuildPlugin help
        """
        # Get uat_path from target engine
        target_engine_path = self.get_target_engine_path()
        if not target_engine_path:
            QMessageBox.warning(
                self,
                self.localize("error_title", "Error"),
                self.localize("help_error_target", "Select target Unreal Engine version.")
            )
            return

        uat_path = os.path.join(target_engine_path, "Engine", "Build", "BatchFiles", "RunUAT.bat")
        if not os.path.exists(uat_path):
            QMessageBox.warning(
                self,
                self.localize("error_title", "Error"),
                self.localize("help_error_uat", "RunUAT.bat file not found at path: {0}", **{"0": uat_path})
            )
            return

        # Start process to get help
        try:
            help_msg = self.localize("help_start", "Getting BuildPlugin help...")
            self.console.append_text(help_msg, "INFO")
            process = QProcess()
            process.finished.connect(lambda code, status: self.handle_help_finished(process, code))
            process.start(uat_path, ["-Help", "BuildPlugin"])
        except Exception as e:
            error_msg = self.localize("help_error", "Error getting help: {0}", **{"0": str(e)})
            self.console.append_text(error_msg, "ERROR")

    def handle_help_finished(self, process: QProcess, exit_code: int) -> None:
        """
        Handle help process completion
        """
        if exit_code == 0:
            output = process.readAllStandardOutput().data().decode('utf-8', errors='replace')
            self.console.append_text(self.localize("help_header", "=== BuildPlugin Help ==="), "INFO")
            for line in output.splitlines():
                if line.strip():
                    self.console.append_text(line, "INFO")
            self.console.append_text(self.localize("help_footer", "=== End of Help ==="), "INFO")
        else:
            error = process.readAllStandardError().data().decode('utf-8', errors='replace')
            error_msg = f"Error getting help (code: {exit_code})"
            self.console.append_text(error_msg, "ERROR")
            if error:
                self.console.append_text(error, "ERROR")

    def show_command(self) -> None:
        """
        Show build command
        """
        # Set parameters in builder to form command
        self.plugin_builder.source_plugin_path = self.plugin_path_edit.text()
        self.plugin_builder.output_folder = self.get_output_path()
        self.plugin_builder.target_engine_path = self.get_target_engine_path()
        self.plugin_builder.additional_params = self.advanced_options

        # Get command
        command = self.plugin_builder.get_command_string()

        if command:
            # Show dialog with command
            dialog = QDialog(self)
            dialog.setWindowTitle(self.localize("command_dialog_title", "Build Command"))
            dialog.setMinimumWidth(600)

            layout = QVBoxLayout(dialog)

            command_label = QLabel(self.localize("command_label", "Command to run in command line:"))
            layout.addWidget(command_label)

            command_text = QTextEdit()
            command_text.setPlainText(command)
            command_text.setReadOnly(True)
            layout.addWidget(command_text)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            dialog.exec()
        else:
            QMessageBox.warning(
                self,
                self.localize("error_title", "Error"),
                self.localize("error_cannot_start_build", "Failed to form build command. Check all build parameters.")
            )

    def build_plugin(self) -> None:
        """
        Start building the plugin
        """
        # Check if all required parameters are present
        plugin_path = self.plugin_path_edit.text()
        output_path = self.get_output_path()
        target_engine_path = self.get_target_engine_path()

        if not plugin_path:
            QMessageBox.warning(
                self,
                self.localize("error_title", "Error"),
                self.localize("error_no_plugin", "No plugin selected for build.")
            )
            return

        if not os.path.exists(plugin_path):
            QMessageBox.warning(
                self,
                self.localize("error_title", "Error"),
                self.localize("error_plugin_not_found", "Plugin file not found: {0}", **{"0": plugin_path})
            )
            return

        if not output_path:
            QMessageBox.warning(
                self,
                self.localize("error_title", "Error"),
                self.localize("error_no_output", "Output path not specified.")
            )
            return

        if not target_engine_path:
            QMessageBox.warning(
                self,
                self.localize("error_title", "Error"),
                self.localize("error_no_target_engine", "Target Unreal Engine version not selected.")
            )
            return

        # Start building
        success = self.plugin_builder.build_plugin(
            plugin_path,
            output_path,
            target_engine_path,
            self.advanced_options
        )

        if not success:
            QMessageBox.warning(
                self,
                self.localize("error_title", "Error"),
                self.localize("error_cannot_start_build", "Failed to start plugin build. Check parameters and logs.")
            )

    def handle_log_message(self, message: str, log_type: str) -> None:
        """
        Handle messages from backend
        """
        self.console.append_text(message, log_type)

    def switch_build_button_state(self, mode: str = "build") -> None:
        """
        Switch the build button between build and abort modes

        :param mode: 'build' or 'abort'
        """
        # Disconnect any existing connections first to avoid multiple connections
        try:
            self.build_button.clicked.disconnect()
        except TypeError:
            # No connections to disconnect
            pass

        if mode == "build":
            # Set to build mode (blue button)
            self.build_button.setText(self.localize("build_button", "Rebuild Plugin"))
            self.build_button.setStyleSheet("""
                QPushButton {
                    background-color: #0078D4;
                    color: white;
                    padding: 8px 16px;
                    font-weight: bold;
                    border-radius: 4px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #106EBE;
                }
                QPushButton:pressed {
                    background-color: #005A9E;
                }
            """)
            self.build_button.clicked.connect(self.build_plugin)

        elif mode == "abort":
            # Set to abort mode (red button)
            self.build_button.setText(self.localize("abort_button", "Abort Build"))
            self.build_button.setStyleSheet("""
                QPushButton {
                    background-color: #D13438;
                    color: white;
                    padding: 8px 16px;
                    font-weight: bold;
                    border-radius: 4px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #C50F1F;
                }
                QPushButton:pressed {
                    background-color: #A80000;
                }
            """)
            self.build_button.clicked.connect(self.cancel_build)

    def handle_build_started(self) -> None:
        """
        Handle build start
        """
        # Switch button to abort mode
        self.switch_build_button_state("abort")

        # Log the build start
        self.console.append_text(self.localize("log_build_start", "Starting plugin build..."), "INFO")

    def cancel_build(self) -> None:
        """
        Cancel the current build process with confirmation
        """
        # Add confirmation dialog
        confirm = QMessageBox.question(
            self,
            self.localize("cancel_build_title", "Cancel Build?"),
            self.localize("cancel_build_message", "Are you sure you want to cancel the current build?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Default to No to prevent accidental cancellations
        )

        if confirm == QMessageBox.Yes:
            if self.plugin_builder.cancel_build():
                # Log the cancellation
                cancelled_msg = self.localize("build_cancelled", "Build cancelled by user")
                self.console.append_text(cancelled_msg, "WARNING")

                # Switch button back to build mode
                self.switch_build_button_state("build")
            else:
                # If cancellation failed (no active process)
                self.console.append_text(
                    self.localize("cancel_failed", "No active build process to cancel."),
                    "WARNING"
                )

    def handle_build_finished(self, success: bool, message: str) -> None:
        """
        Handle build completion
        """
        # Switch button back to build mode
        self.switch_build_button_state("build")

        # Log the result
        log_type = "SUCCESS" if success else "ERROR"
        self.console.append_text(message, log_type)

        if success:
            QMessageBox.information(
                self,
                self.localize("build_success_title", "Build Complete"),
                self.localize("build_success_message", "Plugin successfully built to: {0}",
                              **{"0": self.get_output_path()})
            )


class EnginesFoundEvent(QEvent):
    """
    Custom event for updating engine list in main thread
    """
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, engines: dict[str,str]):
        super().__init__(self.EVENT_TYPE)
        self.engines = engines

    def get_engines(self) -> Dict[str, str]:
        return self.engines


# Override event method to handle custom events
def event(self, e: QEvent) -> bool:
    if e.type() == EnginesFoundEvent.EVENT_TYPE:
        self.update_engines_list(e.get_engines())
        return True
    return super(MainWindow, self).event(e)


MainWindow.event = event