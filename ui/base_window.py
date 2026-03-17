from PySide6.QtCore import Qt, QPoint, QSize, QEvent
from PySide6.QtGui import QColor, QPixmap, QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QGraphicsDropShadowEffect, QFrame, QHBoxLayout, QWidget, QLabel, \
    QPushButton

from core.custom_theme import custom_theme
from core.utils import resource_path


class BaseWindow(QDialog):
    def __init__(self, width=600, height=300, title="Janela"):
        super().__init__()

        #Instâncias
        self.window_layout = None
        self.topbar = None
        self.topbar_layout = None
        self.mic_logo_label = None
        self.window_name_label = None
        self.close_button = None
        self.min_button = None

        self.title = title

        self.setWindowTitle(self.title)
        self.setFixedSize(width, height)

        # Layout Principal
        self.window_layout = QVBoxLayout(self)
        self.window_layout.setContentsMargins(15, 15, 15, 15)
        self.window_layout.setSpacing(0)

        theme = custom_theme()
        self.setStyleSheet(theme)

        # Remove bordas e barra de título
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Variável para guardar posição do mouse ao clicar
        self._posicao_click = QPoint()

        # Aplica Sombra em volta da guia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)  # Quanto mais alto, mais suave
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(255, 255, 255, 40))
        self.setGraphicsEffect(shadow)

        # Cria a Topbar
        self.create_topbar()

    def create_topbar(self):
        self.topbar = QFrame()
        self.topbar.setFixedHeight(40)

        # Habilita a movimentação pela Topbar
        self.topbar.installEventFilter(self)

        self.topbar_layout = QHBoxLayout(self.topbar)
        self.topbar_layout.setContentsMargins(0, 0, 0, 0)
        self.topbar_layout.addStretch()
        self.topbar_layout.setSpacing(20)

        self.window_layout.addWidget(self.topbar)

        container1 = QWidget()
        container1.setFixedHeight(40)
        container1_layout = QHBoxLayout(container1)
        container1_layout.setContentsMargins(10, 0, 10, 0)
        container1_layout.addStretch()
        container1_layout.setSpacing(15)
        self.topbar_layout.addWidget(container1, alignment=Qt.AlignLeft)

        self.mic_logo_label = QLabel()
        self.mic_logo_label.setPixmap(
            QPixmap(resource_path("icons", "logo_icon.svg")).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        container1_layout.addWidget(self.mic_logo_label)

        self.window_name_label = QLabel(self.title)
        container1_layout.addWidget(self.window_name_label)

        self.topbar_layout.addStretch(1)

        container2 = QWidget()
        container2.setFixedHeight(40)
        container2_layout = QHBoxLayout(container2)
        container2_layout.setContentsMargins(0, 0, 0, 0)
        container2_layout.addStretch()
        container2_layout.setSpacing(0)
        self.topbar_layout.addWidget(container2, alignment=Qt.AlignLeft)

        self.close_button = QPushButton("✕")
        self.min_button = QPushButton("−")

        self.close_button.setObjectName("CloseButton")

        self.min_button.clicked.connect(self.showMinimized)
        self.close_button.clicked.connect(self.closeWindow)

        for btn in [self.min_button, self.close_button]:
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("margin: 0; border-radius: 0px; padding: 0; font-size: 14pt; font-weight: normal;")
            container2_layout.addWidget(btn, alignment=Qt.AlignLeft)

    def create_button(self, button, layout, label="", btn_h=30, btn_w=30, btn_alignment=Qt.AlignRight,
                      icon_path="", icon_h=25, icon_w=25, tooltip=""):
        if button is None:
            button = QPushButton(label)
        button.setFixedSize(btn_h, btn_w)
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(icon_h, icon_w))
        if tooltip:
            button.setToolTip(tooltip)
        layout.addWidget(button, alignment=btn_alignment)
        return button

    # Movimentação da Janela
    def eventFilter(self, source, event):
        if source == self.topbar:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._posicao_click = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True
            elif event.type() == QEvent.MouseMove and event.buttons() & Qt.LeftButton:
                self.move(event.globalPosition().toPoint() - self._posicao_click)
                return True
        return super().eventFilter(source, event)

    def closeWindow(self):
        self.close()