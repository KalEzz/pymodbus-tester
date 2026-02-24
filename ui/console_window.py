import sys

from PySide6.QtCore import Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QTextEdit, QFrame, QHBoxLayout
import sys

from ui.base_window import BaseWindow


class ConsoleWindow(BaseWindow):
    def __init__(self):
        super().__init__(title="Console Debug", width=900, height=500)

        self.console = ConsoleWidget()
        self.console_frame = QFrame()

        self.console_frame_layout = QHBoxLayout(self.console_frame)
        self.console_frame_layout.setContentsMargins(0, 0, 0, 0)

        self.console_frame_layout.addWidget(self.console)

        self.window_layout.addWidget(self.console_frame)

        # Guarda stdout original
        self._original_stdout = sys.__stdout__
        self._original_stderr = sys.__stderr__

        # Duplica saída
        sys.stdout = TeeOutput(self._original_stdout, self.console)
        sys.stderr = TeeOutput(self._original_stderr, self.console)

    def closeEvent(self, event):
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        self.deleteLater()
        super().closeEvent(event)


class ConsoleWidget(QTextEdit):
    append_text = Signal(str)

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.append_text.connect(self._append_text)
        self.setObjectName("ConsoleText")

    def write(self, text):
        self.append_text.emit(text)

    def _append_text(self, text):
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(text)

    def flush(self):
        pass



class TeeOutput:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for stream in self.streams:
            try:
                stream.write(text)
            except Exception:
                pass

    def flush(self):
        for stream in self.streams:
            try:
                stream.flush()
            except Exception:
                pass
