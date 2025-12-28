"""
Drop zone overlay and base widget for drag-and-drop functionality.
"""
from pathlib import Path
from typing import Optional, List, Callable
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import (
    Qt, 
    Signal, 
    QPropertyAnimation, 
    Property, 
    QEasingCurve,
    QMimeData,
    QRectF,
)
from PySide6.QtGui import (
    QPainter, 
    QColor, 
    QPen, 
    QFont,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
)

from ..styles import COLORS, FONTS, RADIUS
from ..icons import Icons
from ue_plugin_builder.core import tr


class DropOverlay(QWidget):
    """
    Animated overlay that appears during drag-and-drop.
    
    Features:
    - Fade in/out animation
    - Visual feedback for valid/invalid drops
    - Centered icon and text
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._opacity = 0.0
        self._is_valid = True
        
        # Animation
        self._animation = QPropertyAnimation(self, b"opacity")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()
    
    def get_opacity(self) -> float:
        return self._opacity
    
    def set_opacity(self, value: float) -> None:
        self._opacity = value
        self.update()
    
    opacity = Property(float, get_opacity, set_opacity)
    
    def show_overlay(self, valid: bool = True) -> None:
        """Show the overlay with animation."""
        self._is_valid = valid
        self.show()
        self.raise_()
        self.setGeometry(self.parent().rect())
        
        self._animation.stop()
        self._animation.setStartValue(self._opacity)
        self._animation.setEndValue(1.0)
        self._animation.start()
    
    def hide_overlay(self) -> None:
        """Hide the overlay with animation."""
        self._animation.stop()
        self._animation.setStartValue(self._opacity)
        self._animation.setEndValue(0.0)
        self._animation.finished.connect(self._on_animation_finished)
        self._animation.start()
    
    def _on_animation_finished(self) -> None:
        """Handle animation completion."""
        self._animation.finished.disconnect(self._on_animation_finished)
        if self._opacity <= 0.01:
            self.hide()
    
    def paintEvent(self, event) -> None:
        """Paint the overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Colors based on validity
        if self._is_valid:
            bg_color = QColor(34, 211, 238, int(25 * self._opacity))  # cyan-400/10
            border_color = QColor(34, 211, 238, int(180 * self._opacity))
            icon_color = f"rgba(34, 211, 238, {self._opacity})"
            icon_name = "UPLOAD"
            text = None  # No text for valid drops
        else:
            bg_color = QColor(248, 113, 113, int(25 * self._opacity))  # red-400/10
            border_color = QColor(248, 113, 113, int(180 * self._opacity))
            icon_color = f"rgba(248, 113, 113, {self._opacity})"
            icon_name = "X_CIRCLE"
            text = tr("invalid_drop_file")
        
        # Background
        painter.fillRect(self.rect(), bg_color)
        
        # Dashed border
        pen = QPen(border_color, 2, Qt.PenStyle.DashLine)
        pen.setDashPattern([8, 4])
        painter.setPen(pen)
        margin = 16
        painter.drawRoundedRect(
            margin, margin,
            self.width() - 2 * margin,
            self.height() - 2 * margin,
            8, 8
        )
        
        # Icon - draw SVG pixmap
        icon_size = 48
        icon_pixmap = Icons.get_pixmap(icon_name, icon_size, icon_color)
        icon_x = (self.width() - icon_size) // 2
        # Center icon if no text, otherwise offset up
        if text:
            icon_y = (self.height() // 2) - icon_size - 8
        else:
            icon_y = (self.height() - icon_size) // 2
        painter.setOpacity(self._opacity)
        painter.drawPixmap(icon_x, icon_y, icon_pixmap)
        painter.setOpacity(1.0)
        
        # Text (only for invalid drops)
        if text:
            text_color = QColor(border_color)
            text_color.setAlphaF(self._opacity)
            painter.setPen(text_color)
            text_font = QFont(FONTS['family'].split(',')[0].strip())
            text_font.setPixelSize(14)
            text_font.setWeight(QFont.Weight.Medium)
            painter.setFont(text_font)
            painter.drawText(
                self.rect().adjusted(0, 40, 0, 0),
                Qt.AlignmentFlag.AlignCenter,
                text
            )


class DropZoneWidget(QWidget):
    """
    Base widget class that provides drag-and-drop functionality.
    
    Subclass this to create widgets that accept file drops.
    
    Features:
    - Automatic overlay management
    - File type validation
    - Directory support
    - Callback-based drop handling
    """
    
    file_dropped = Signal(str)
    
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        valid_extensions: Optional[List[str]] = None,
        allow_directories: bool = False,
    ):
        super().__init__(parent)
        self._valid_extensions = valid_extensions or []
        self._allow_directories = allow_directories
        self._drop_callback: Optional[Callable[[str], None]] = None
        self._overlay: Optional[DropOverlay] = None
        
        self.setAcceptDrops(True)
    
    def setup_drop_overlay(self) -> None:
        """Initialize the drop overlay. Call this after setting up child widgets."""
        self._overlay = DropOverlay(self)
        self._overlay.setGeometry(self.rect())
    
    def set_drop_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback to be called when a file is dropped."""
        self._drop_callback = callback
    
    def _is_valid_drop(self, mime_data: QMimeData) -> bool:
        """Check if the drop data is valid."""
        if not mime_data.hasUrls():
            return False
        
        for url in mime_data.urls():
            if not url.isLocalFile():
                continue
            
            path = Path(url.toLocalFile())
            
            # Check if directory
            if path.is_dir():
                if self._allow_directories:
                    # Check if directory contains valid files
                    for ext in self._valid_extensions:
                        if list(path.glob(f"*{ext}")):
                            return True
                continue
            
            # Check file extension
            if not self._valid_extensions:
                return True
            
            if path.suffix.lower() in [e.lower() for e in self._valid_extensions]:
                return True
        
        return False
    
    def _find_target_file(self, mime_data: QMimeData) -> Optional[str]:
        """Find the target file from dropped data."""
        for url in mime_data.urls():
            if not url.isLocalFile():
                continue
            
            path = Path(url.toLocalFile())
            
            # If directory, find first valid file
            if path.is_dir():
                for ext in self._valid_extensions:
                    files = list(path.glob(f"*{ext}"))
                    if files:
                        return str(files[0])
                continue
            
            # Check file extension
            if not self._valid_extensions:
                return str(path)
            
            if path.suffix.lower() in [e.lower() for e in self._valid_extensions]:
                return str(path)
        
        return None
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter."""
        if event.mimeData().hasUrls():
            is_valid = self._is_valid_drop(event.mimeData())
            event.acceptProposedAction()
            
            if self._overlay:
                self._overlay.show_overlay(valid=is_valid)
        else:
            event.ignore()
    
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Handle drag move - required to maintain drop acceptance."""
        event.acceptProposedAction()
    
    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """Handle drag leave."""
        if self._overlay:
            self._overlay.hide_overlay()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop."""
        if self._overlay:
            self._overlay.hide_overlay()
        
        target_path = self._find_target_file(event.mimeData())
        
        if target_path:
            event.acceptProposedAction()
            self.file_dropped.emit(target_path)
            
            if self._drop_callback:
                self._drop_callback(target_path)
        else:
            event.ignore()
    
    def resizeEvent(self, event) -> None:
        """Handle resize to update overlay geometry."""
        super().resizeEvent(event)
        if self._overlay:
            self._overlay.setGeometry(self.rect())
