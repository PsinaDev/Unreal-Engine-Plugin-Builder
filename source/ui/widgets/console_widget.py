"""
Console output widget with syntax highlighting.
"""
import re
import random
import math
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QFrame,
    QApplication,
    QGraphicsOpacityEffect,
)
from PySide6.QtCore import (
    Qt, QTimer, Slot, QPropertyAnimation, 
    QEasingCurve, Property, QPoint, QPointF, QRectF,
)
from PySide6.QtGui import (
    QTextCharFormat,
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextDocument,
    QPainter,
    QPainterPath,
    QScreen,
)

from ..styles import COLORS, FONTS, RADIUS
from ..icons import Icons
from ue_plugin_builder.core import LogLevel, LogMessage, tr


# Combo messages for copy easter egg
COMBO_MESSAGES = [
    "combo_copy_0",   # Скопировано!
    "combo_copy_1",   # Двойное копирование!
    "combo_copy_2",   # Тройное копирование!
    "combo_copy_3",   # Комбо копирование!
    "combo_copy_4",   # Мега копирование!
    "combo_copy_5",   # Супер копирование!
    "combo_copy_6",   # Ультра копирование!
    "combo_copy_7",   # ГИГА копирование!!!
    "combo_copy_8",   # ☆ ЛЕГЕНДАРНОЕ ☆
    "combo_copy_9",   # ✦ БОЖЕСТВЕННОЕ ✦
    "combo_copy_10",  # ⚡ КОСМИЧЕСКОЕ ⚡
    "combo_copy_11",  # 🔥 АПОКАЛИПСИС 🔥
]

# Post-limit messages (after max combo reached)
POST_LIMIT_MESSAGES = [
    "combo_post_0",   # Может уже хватит?
    "combo_post_1",   # Серьёзно, прекрати
    "combo_post_2",   # Последнее предупреждение!
    "combo_post_3",   # Кнопка будет отобрана через...
]


class ConfettiParticle:
    """A single confetti particle."""
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-15, -8)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-10, 10)
        self.size = random.uniform(6, 12)
        self.color = QColor(random.choice([
            "#22d3ee",  # cyan
            "#f472b6",  # pink
            "#a78bfa",  # purple
            "#34d399",  # green
            "#fbbf24",  # yellow
            "#f87171",  # red
            "#60a5fa",  # blue
        ]))
        self.gravity = 0.4
        self.drag = 0.98
        self.life = 1.0
        self.decay = random.uniform(0.008, 0.015)
        # Shape: 0 = rect, 1 = circle, 2 = star
        self.shape = random.randint(0, 2)
    
    def update(self) -> bool:
        """Update particle position. Returns False if particle is dead."""
        self.vy += self.gravity
        self.vx *= self.drag
        self.x += self.vx
        self.y += self.vy
        self.rotation += self.rotation_speed
        self.life -= self.decay
        return self.life > 0
    
    def draw(self, painter: QPainter) -> None:
        """Draw the particle."""
        if self.life <= 0:
            return
        
        painter.save()
        painter.translate(self.x, self.y)
        painter.rotate(self.rotation)
        
        color = QColor(self.color)
        color.setAlphaF(min(1.0, self.life * 2))
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        half = self.size / 2
        
        if self.shape == 0:
            # Rectangle
            painter.drawRect(QRectF(-half, -half/2, self.size, self.size/2))
        elif self.shape == 1:
            # Circle
            painter.drawEllipse(QPointF(0, 0), half, half)
        else:
            # Star
            path = QPainterPath()
            for i in range(5):
                angle = math.radians(i * 72 - 90)
                outer = QPointF(math.cos(angle) * half, math.sin(angle) * half)
                inner_angle = math.radians(i * 72 - 90 + 36)
                inner = QPointF(math.cos(inner_angle) * half * 0.4, 
                               math.sin(inner_angle) * half * 0.4)
                if i == 0:
                    path.moveTo(outer)
                else:
                    path.lineTo(outer)
                path.lineTo(inner)
            path.closeSubpath()
            painter.drawPath(path)
        
        painter.restore()


class ConfettiWidget(QWidget):
    """Transparent overlay widget for confetti animation."""
    
    def __init__(self):
        super().__init__(None)
        
        # Make it a transparent overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        self.particles: List[ConfettiParticle] = []
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_particles)
        self._timer.setInterval(16)  # ~60 FPS
    
    def launch(self, global_pos: QPoint) -> None:
        """Launch confetti from a global screen position."""
        # Get the screen containing the point
        screen = QApplication.screenAt(global_pos)
        if not screen:
            screen = QApplication.primaryScreen()
        
        screen_geo = screen.geometry()
        self.setGeometry(screen_geo)
        
        # Convert global pos to local
        local_x = global_pos.x() - screen_geo.x()
        local_y = global_pos.y() - screen_geo.y()
        
        # Create particles
        for _ in range(80):
            self.particles.append(ConfettiParticle(local_x, local_y))
        
        self.show()
        self._timer.start()
    
    def _update_particles(self) -> None:
        """Update all particles."""
        self.particles = [p for p in self.particles if p.update()]
        
        if not self.particles:
            self._timer.stop()
            self.hide()
        else:
            self.update()
    
    def paintEvent(self, event) -> None:
        """Paint all particles."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for particle in self.particles:
            particle.draw(painter)


class ConsoleHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for console output.
    """
    
    def __init__(self, document: QTextDocument):
        super().__init__(document)
        self._rules: List[tuple] = []
        self._setup_rules()
    
    def _setup_rules(self) -> None:
        """Set up highlighting rules."""
        # Success patterns - green
        success_format = QTextCharFormat()
        success_format.setForeground(QColor(COLORS['success']))
        
        success_patterns = [
            r'\[SUCCESS\]',
            r'(?i)\bsuccess(ful(ly)?)?\b',
            r'(?i)\bcomplete(d)?\b',
            r'(?i)\bfinish(ed)?\b',
            r'(?i)\bdone\b',
            r'(?i)\bbuilt\b',
            r'(?i)\bfound\s+\d+\s+engine',
            r'(?i)\bregistered\s+engine\b',
        ]
        for pattern in success_patterns:
            self._rules.append((re.compile(pattern), success_format))
        
        # Error patterns - red
        error_format = QTextCharFormat()
        error_format.setForeground(QColor(COLORS['error']))
        
        error_patterns = [
            r'\[ERROR\]',
            r'(?i)\berror\b',
            r'(?i)\bfailed?\b',
            r'(?i)\bcrash(ed)?\b',
            r'(?i)\bexception\b',
            r'(?i)\bcritical\b',
            r'(?i)\bfatal\b',
            r'\bLNK\d+\b',
            r'\bC\d{4}\b',
            r'\bMSB\d+\b',
        ]
        for pattern in error_patterns:
            self._rules.append((re.compile(pattern), error_format))
        
        # Warning patterns - amber
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor(COLORS['warning']))
        
        warning_patterns = [
            r'\[WARNING\]',
            r'(?i)\bwarn(ing)?\b',
            r'(?i)\bcaution\b',
            r'(?i)\bskip(ped|ping)?\b',
            r'(?i)\bdeprecated\b',
        ]
        for pattern in warning_patterns:
            self._rules.append((re.compile(pattern), warning_format))
        
        # Info patterns - cyan
        info_format = QTextCharFormat()
        info_format.setForeground(QColor(COLORS['accent_primary']))
        
        info_patterns = [
            r'\[INFO\]',
            r'(?i)\bsearching\b',
            r'(?i)\bstarting\b',
            r'(?i)\bchecking\b',
            r'(?i)\bbuilding\b',
            r'(?i)\bcompiling\b',
            r'(?i)\bloading\b',
        ]
        for pattern in info_patterns:
            self._rules.append((re.compile(pattern), info_format))
        
        # Path patterns - dimmed
        path_format = QTextCharFormat()
        path_format.setForeground(QColor(COLORS['text_dim']))
        
        path_patterns = [
            r'[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*',
            r'(?:/[^/\s]+)+',
        ]
        for pattern in path_patterns:
            self._rules.append((re.compile(pattern), path_format))
        
        # Progress patterns - cyan bold
        progress_format = QTextCharFormat()
        progress_format.setForeground(QColor(COLORS['accent_primary']))
        progress_format.setFontWeight(QFont.Bold)
        
        progress_patterns = [
            r'\[\d+/\d+\]',
            r'\b\d+%\b',
        ]
        for pattern in progress_patterns:
            self._rules.append((re.compile(pattern), progress_format))
    
    def highlightBlock(self, text: str) -> None:
        """Apply highlighting to a block of text."""
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class CopiedTooltip(QLabel):
    """Animated 'Copied!' tooltip with combo support."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(tr("copied"), parent)
        self._base_style = """
            QLabel {{
                background-color: {bg};
                color: {fg};
                font-size: {size};
                font-weight: 600;
                padding: 4px 10px;
                border-radius: 6px;
            }}
        """
        self._set_style(COLORS['success'], COLORS['bg_primary'], FONTS['size_xs'])
        self.setAlignment(Qt.AlignCenter)
        self.hide()
        
        # Opacity effect
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)
        
        # Animation
        self._animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._animation.setDuration(300)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.finished.connect(self._on_animation_finished)
        
        # Hide timer
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._start_fade_out)
    
    def _set_style(self, bg: str, fg: str, size: str) -> None:
        """Set the tooltip style."""
        self.setStyleSheet(self._base_style.format(bg=bg, fg=fg, size=size))
    
    def show_at(self, anchor_right: int, anchor_y: int, text: str = None, combo_level: int = 0) -> None:
        """
        Show tooltip anchored by its RIGHT edge.
        
        Args:
            anchor_right: X position where the RIGHT edge of tooltip should be
            anchor_y: Y position (center)
            text: Text to display
            combo_level: Combo level for styling (negative = special styles)
        """
        if text:
            self.setText(text)
        
        # Style based on combo level
        if combo_level == -3:
            # Final - button gone
            self._set_style("#ef4444", "#000000", "14px")  # Red with black text
        elif combo_level == -2:
            # Countdown
            self._set_style("#f97316", "#000000", "16px")  # Orange with black text
        elif combo_level == -1:
            # Warning messages
            self._set_style("#ef4444", "#000000", "12px")  # Red with black text
        elif combo_level >= 10:
            self._set_style("#f472b6", "#000000", "14px")  # Pink - legendary
        elif combo_level >= 7:
            self._set_style("#a78bfa", "#000000", "13px")  # Purple - epic
        elif combo_level >= 5:
            self._set_style("#fbbf24", "#000000", "13px")  # Gold - rare
        elif combo_level >= 3:
            self._set_style("#22d3ee", "#000000", "12px")  # Cyan - combo
        else:
            self._set_style(COLORS['success'], COLORS['bg_primary'], FONTS['size_xs'])
        
        # IMPORTANT: adjustSize AFTER setting text and style
        self.adjustSize()
        
        # Position so RIGHT edge is at anchor_right
        tooltip_width = self.width()
        tooltip_height = self.height()
        
        pos = QPoint(
            anchor_right - tooltip_width,  # Right edge aligned
            anchor_y - tooltip_height // 2  # Vertically centered
        )
        
        self.move(pos)
        self._opacity_effect.setOpacity(1.0)
        self.show()
        self.raise_()
        
        # Longer display for higher combos, shorter for warnings
        if combo_level < 0:
            display_time = 800
        else:
            display_time = 1000 + (combo_level * 200)
        self._hide_timer.start(min(display_time, 3000))
    
    def _start_fade_out(self) -> None:
        """Start fade out animation."""
        self._animation.setStartValue(1.0)
        self._animation.setEndValue(0.0)
        self._animation.start()
    
    def _on_animation_finished(self) -> None:
        """Hide when animation finishes."""
        if self._opacity_effect.opacity() < 0.1:
            self.hide()


class ConsoleWidget(QWidget):
    """
    Console output widget with header and controls.
    """
    
    # Combo timeout in milliseconds
    COMBO_TIMEOUT = 800
    # Combo level that triggers confetti
    CONFETTI_THRESHOLD = 8
    # Max combo level before post-limit messages
    MAX_COMBO = len(COMBO_MESSAGES) - 1
    # How many times to repeat last combo message
    REPEAT_LAST_COMBO = 3
    # Countdown start value
    COUNTDOWN_START = 3
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._buffer: List[str] = []
        self._buffer_timer: Optional[QTimer] = None
        
        # Combo tracking
        self._combo_count = 0
        self._post_limit_count = 0  # Clicks after max combo
        self._countdown_value = 0
        self._button_hidden = False
        
        self._combo_timer = QTimer(self)
        self._combo_timer.setSingleShot(True)
        self._combo_timer.timeout.connect(self._reset_combo)
        
        # Confetti overlay (lazy init)
        self._confetti: Optional[ConfettiWidget] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(24, 24, 27, 0.5);
                border: none;
                border-bottom: 1px solid {COLORS['border_default']};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 8, 16, 8)
        header_layout.setSpacing(8)
        
        # Title
        title = QLabel(tr("console_output"))
        title.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: {FONTS['size_sm']};
            font-weight: 500;
            background: transparent;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Copy button (icon only)
        self._copy_btn = QPushButton()
        self._copy_btn.setIcon(Icons.get_icon("COPY", 14, COLORS['text_dim']))
        self._copy_btn.setFixedSize(28, 24)
        self._copy_btn.setToolTip(tr("copy_tooltip"))
        self._copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_tertiary']};
            }}
        """)
        self._copy_btn.clicked.connect(self._copy_to_clipboard)
        self._copy_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(self._copy_btn)
        
        layout.addWidget(header)
        
        # Text area
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setFont(QFont(FONTS['family_mono'], 10))
        self._text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_primary']};
                border: none;
                color: {COLORS['text_muted']};
                padding: 8px;
            }}
        """)
        
        # Apply syntax highlighter
        self._highlighter = ConsoleHighlighter(self._text_edit.document())
        
        layout.addWidget(self._text_edit, 1)
        
        # Copied tooltip
        self._copied_tooltip = CopiedTooltip(self)
        
        # Setup buffer timer for batched updates
        self._buffer_timer = QTimer(self)
        self._buffer_timer.setInterval(30)
        self._buffer_timer.timeout.connect(self._flush_buffer)
    
    def _reset_combo(self) -> None:
        """Reset the combo counter."""
        self._combo_count = 0
        self._post_limit_count = 0
        self._countdown_value = 0
    
    def _get_combo_message(self) -> tuple[str, int]:
        """
        Get the message and effective combo level for current state.
        Returns (message_key, combo_level_for_styling)
        """
        if self._combo_count <= self.MAX_COMBO:
            # Normal combo progression
            return tr(COMBO_MESSAGES[self._combo_count]), self._combo_count
        
        # Post-limit phase
        extra_clicks = self._combo_count - self.MAX_COMBO - 1
        
        if extra_clicks < self.REPEAT_LAST_COMBO:
            # Repeat last combo message
            return tr(COMBO_MESSAGES[-1]), self.MAX_COMBO
        
        # Post-limit messages
        post_index = extra_clicks - self.REPEAT_LAST_COMBO
        
        if post_index < len(POST_LIMIT_MESSAGES) - 1:
            return tr(POST_LIMIT_MESSAGES[post_index]), -1  # -1 = warning style
        
        # Countdown phase
        countdown_clicks = post_index - (len(POST_LIMIT_MESSAGES) - 1)
        countdown_value = self.COUNTDOWN_START - countdown_clicks
        
        if countdown_value > 0:
            return f"{countdown_value}...", -2  # -2 = countdown style
        else:
            return tr("combo_button_gone"), -3  # -3 = final style
    
    def _launch_confetti(self) -> None:
        """Launch confetti animation."""
        if self._confetti is None:
            self._confetti = ConfettiWidget()
        
        # Launch from button position
        btn_global = self._copy_btn.mapToGlobal(QPoint(
            self._copy_btn.width() // 2,
            self._copy_btn.height() // 2
        ))
        self._confetti.launch(btn_global)
    
    def append(self, text: str, level: LogLevel = LogLevel.INFO) -> None:
        """Append text to the console."""
        prefix = f"[{level.name}]"
        self._buffer.append(f"{prefix} {text}")
        
        if not self._buffer_timer.isActive():
            self._buffer_timer.start()
    
    def append_log(self, message: LogMessage) -> None:
        """Append a LogMessage to the console."""
        self.append(message.text, message.level)
    
    def append_raw(self, text: str) -> None:
        """Append raw text without prefix."""
        self._buffer.append(text)
        
        if not self._buffer_timer.isActive():
            self._buffer_timer.start()
    
    @Slot()
    def _flush_buffer(self) -> None:
        """Flush buffered text to the widget."""
        if not self._buffer:
            self._buffer_timer.stop()
            return
        
        # Apply syntax highlighting and join
        highlighted_lines = [self._highlight_line(line) for line in self._buffer]
        html = '<br>'.join(highlighted_lines) + '<br>'
        self._buffer.clear()
        
        cursor = self._text_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertHtml(html)
        
        scrollbar = self._text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        self._buffer_timer.stop()
    
    def _highlight_line(self, line: str) -> str:
        """Apply syntax highlighting to a line."""
        import re
        import html as html_module
        
        # Escape HTML first
        escaped = html_module.escape(line)
        
        # Colors
        cyan = "#22d3ee"      # Parameters, keywords
        yellow = "#fbbf24"    # Placeholders
        green = "#34d399"     # Success
        red = "#f87171"       # Errors
        dim = "#71717a"       # Comments, optional
        muted = "#a1a1aa"     # Default values
        purple = "#c084fc"    # Examples
        
        # Check for [INFO], [ERROR], etc. prefix first
        prefix_match = re.match(r'^(\[INFO\]|\[ERROR\]|\[WARNING\]|\[SUCCESS\]|\[DEBUG\])\s*', escaped)
        prefix_html = ""
        rest = escaped
        
        if prefix_match:
            prefix = prefix_match.group(1)
            rest = escaped[prefix_match.end():]
            prefix_colors = {
                "[INFO]": cyan,
                "[ERROR]": red,
                "[WARNING]": yellow,
                "[SUCCESS]": green,
                "[DEBUG]": dim,
            }
            color = prefix_colors.get(prefix, dim)
            prefix_html = f'<span style="color:{color}">{prefix}</span> '
        
        # Apply highlighting patterns to the rest
        result = rest
        
        # Parameters: -ParameterName (at start of word or after space)
        result = re.sub(
            r'(\s|^)(-[A-Za-z_][A-Za-z0-9_]*)',
            rf'\1<span style="color:{cyan}">\2</span>',
            result
        )
        
        # Placeholders: <Something> or <Something[s]>
        result = re.sub(
            r'&lt;([^&]+)&gt;',
            rf'<span style="color:{yellow}">&lt;\1&gt;</span>',
            result
        )
        
        # Examples in parentheses: (eg. ...) or (optional)
        result = re.sub(
            r'\((eg\.[^)]+)\)',
            rf'<span style="color:{purple}">(\1)</span>',
            result
        )
        result = re.sub(
            r'\((optional)\)',
            rf'<span style="color:{dim}">(\1)</span>',
            result
        )
        
        # Success/Error/Warning keywords (case insensitive, whole word)
        result = re.sub(
            r'\b(Success|Succeeded|Completed|Finished)\b',
            rf'<span style="color:{green}">\1</span>',
            result,
            flags=re.IGNORECASE
        )
        result = re.sub(
            r'\b(Error|Failed|Failure)\b',
            rf'<span style="color:{red}">\1</span>',
            result,
            flags=re.IGNORECASE
        )
        result = re.sub(
            r'\b(Warning)\b',
            rf'<span style="color:{yellow}">\1</span>',
            result,
            flags=re.IGNORECASE
        )
        
        # Starting, Initializing, Running, Using, Parsing
        result = re.sub(
            r'\b(Starting|Initializing|Running|Using|Parsing|Building|Compiling)\b',
            rf'<span style="color:{cyan}">\1</span>',
            result
        )
        
        # Default keyword
        result = re.sub(
            r'\b(Default)\b',
            rf'<span style="color:{muted}">\1</span>',
            result
        )
        
        # Version numbers: X.Y.Z or X.Y
        result = re.sub(
            r'\b(\d+\.\d+(?:\.\d+)?)\b',
            rf'<span style="color:{muted}">\1</span>',
            result
        )
        
        return prefix_html + result
    
    def clear(self) -> None:
        """Clear the console."""
        self._buffer.clear()
        self._text_edit.clear()
    
    def _copy_to_clipboard(self) -> None:
        """Copy console content to clipboard and show animation."""
        if self._button_hidden:
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self._text_edit.toPlainText())
        
        # Update combo
        if self._combo_timer.isActive():
            self._combo_count += 1
        else:
            self._combo_count = 0
        
        # Restart combo timer
        self._combo_timer.start(self.COMBO_TIMEOUT)
        
        # Get combo message and style level
        message, style_level = self._get_combo_message()
        
        # Calculate anchor position (left edge of button with gap)
        btn_pos = self._copy_btn.mapTo(self, QPoint(0, 0))
        anchor_right = btn_pos.x() - 8  # 8px gap to the left of button
        anchor_y = btn_pos.y() + self._copy_btn.height() // 2  # Vertical center
        
        self._copied_tooltip.show_at(anchor_right, anchor_y, message, style_level)
        
        # Launch confetti at high combo (but not during warnings)
        if self._combo_count >= self.CONFETTI_THRESHOLD and style_level >= 0:
            self._launch_confetti()
        
        # Hide button after countdown reaches 0
        if style_level == -3:
            self._button_hidden = True
            self._copy_btn.setVisible(False)
    
    def get_text(self) -> str:
        """Get all console text."""
        return self._text_edit.toPlainText()
