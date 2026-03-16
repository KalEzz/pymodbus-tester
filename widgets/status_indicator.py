from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt

class StatusIndicator(QWidget):
    def __init__(self, color="#7f8c8d", parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedSize(14, 14)
        self.set_tooltip()

        self.COLORS = {
            "RUNNING": "#2ecc71",
            "CONNECTING": "#00bfff",
            "ERROR": "#e74c3c",
            "STOPPED": "#7f8c8d",
            "OFFLINE": "#f1c40f"
        }

    def set_status(self, status):
        color = self.COLORS.get(status, "#7f8c8d")

        self.color = QColor(color)
        self.update()

    def set_tooltip(self, status="STOPPED"):
        self.setToolTip(f"{status}")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())