from PySide6.QtWidgets import QTextEdit, QWidget
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor, QSyntaxHighlighter, QFont, QTextDocument
from PySide6.QtCore import QRegularExpression, QTimer

from typing import Optional

from source.frontend.localization import LocalizationManager


class ConsoleHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for the console
    """

    def __init__(self, document: QTextDocument, localization: Optional[LocalizationManager] = None) -> None:
        super().__init__(document)
        self.localization = localization
        self.highlighting_rules = []
        self.setup_highlighting_rules()

    def setup_highlighting_rules(self) -> None:
        """
        Set up syntax highlighting rules
        """
        # Error format (red)
        error_format = QTextCharFormat()
        error_format.setForeground(QColor("#FF5252"))

        error_pattern = r"\[ERROR\].*|\[ОШИБКА\].*|(^|\s)error(\s|$)|(^|\s)ошибка(\s|$)|(^|\s)failed(\s|$)"
        self.highlighting_rules.append((QRegularExpression(error_pattern), error_format))

        # Warning format (orange)
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor("#FFA726"))

        warning_pattern = r"\[WARNING\].*|\[ПРЕДУПРЕЖДЕНИЕ\].*|(^|\s)warning(\s|$)|(^|\s)предупреждение(\s|$)"
        self.highlighting_rules.append((QRegularExpression(warning_pattern), warning_format))

        # Success format (green)
        success_format = QTextCharFormat()
        success_format.setForeground(QColor("#66BB6A"))

        success_pattern = r"\[SUCCESS\].*|\[УСПЕХ\].*|(^|\s)success(\s|$)|(^|\s)успешно(\s|$)|(^|\s)completed(\s|$)"
        self.highlighting_rules.append((QRegularExpression(success_pattern), success_format))

        # Info format (blue)
        info_format = QTextCharFormat()
        info_format.setForeground(QColor("#42A5F5"))

        info_pattern = r"\[INFO\].*|\[ИНФО\].*"
        self.highlighting_rules.append((QRegularExpression(info_pattern), info_format))

        # Command format (purple)
        command_format = QTextCharFormat()
        command_format.setForeground(QColor("#BA68C8"))

        command_pattern = r"RunUAT|BuildPlugin"
        self.highlighting_rules.append((QRegularExpression(command_pattern), command_format))

        # Path format (teal)
        path_format = QTextCharFormat()
        path_format.setForeground(QColor("#4DB6AC"))

        path_pattern = r"[A-Za-z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]*|\.uplugin|\.bat"
        self.highlighting_rules.append((QRegularExpression(path_pattern), path_format))

    def highlightBlock(self, text: str) -> None:
        """
        Highlight a block of text
        """
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class ConsoleWidget(QTextEdit):
    """
    Console widget with syntax highlighting
    """

    def __init__(self, parent: Optional[QWidget] = None, localization: Optional[LocalizationManager] = None) -> None:
        super().__init__(parent)
        self.localization = localization

        # Set up appearance
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2D2D30;
                color: #CCCCCC;
                border: 1px solid #3F3F46;
                border-radius: 4px;
            }
        """)

        # Set monospace font
        font = QFont("Consolas", 9)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        # Create and apply syntax highlighting
        self.highlighter = ConsoleHighlighter(self.document(), localization)

        # Buffer for adding text (for performance optimization)
        self.buffer = []
        self.buffer_timer = QTimer(self)
        self.buffer_timer.timeout.connect(self._flush_buffer)
        self.buffer_timer.setInterval(100)  # Update every 100ms

    def append_text(self, message: str, log_type: Optional[str] = None) -> None:
        """
        Add text to the console with syntax highlighting

        :param message: Text to add
        :param log_type: Log type (INFO, ERROR, WARNING, SUCCESS)
        """
        # Add to buffer
        self.buffer.append((message, log_type))

        # Start timer if not already running
        if not self.buffer_timer.isActive():
            self.buffer_timer.start()

    def _flush_buffer(self) -> None:
        """
        Output accumulated buffer to the console
        """
        if not self.buffer:
            self.buffer_timer.stop()
            return

        # Remember scroll position
        scrollbar = self.verticalScrollBar()
        at_bottom = scrollbar.value() == scrollbar.maximum()

        # Set cursor at the end of text
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

        # Add all messages from the buffer
        for message, log_type in self.buffer:
            # If log type is passed, add prefix with localized tag
            if log_type and not (message.startswith("[") and "]" in message):
                # Get localized log type tag
                log_tag = f"log_{log_type.lower()}"
                if self.localization:
                    localized_log_type = self.localization(log_tag, log_type.upper())
                else:
                    localized_log_type = log_type.upper()

                message = f"[{localized_log_type}] {message}"

            # Add text with line break
            cursor.insertText(message + "\n")

        # Clear buffer
        self.buffer.clear()

        # Scroll to the end if console was at the bottom
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def clear_console(self) -> None:
        """
        Clear console contents
        """
        super().clear()
        self.buffer.clear()
        if self.buffer_timer.isActive():
            self.buffer_timer.stop()