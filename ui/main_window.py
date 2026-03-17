import asyncio

from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QFrame, QHBoxLayout, QGridLayout, QScrollArea
from PySide6.QtCore import Qt, QPoint, QEvent, QRect, QTimer

from core.custom_theme import custom_theme

from config.config_manager import load_program_settings, load_devices, save_devices, save_program_settings
from models.device import Device
from ui.config_window import DeviceConfigWindow, ConfigWindow
from ui.console_window import ConsoleWindow

from core.utils import *
from ui.device_monitor_window import DeviceMonitorWindow
from widgets.status_indicator import StatusIndicator


class App(QWidget):
    def __init__(self, runtime):
        super().__init__()
        self.runtime = runtime

        self.program_version = '0.2.1'

        #Criação da Pasta de Leitura
        create_directory('/Desktop/LeiturasPyModbusTester')

        #self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        #Carrega as Configurações do Programa
        self.program_settings = load_program_settings()
        self.devices = load_devices()

        # Instância dos Frames Principais
        self.top_toolbar = None
        self.top_toolbar_layout = None
        self.devices_frame = None
        self.devices_frame_layout = None
        self.scroll_device_frame = None
        self.devices_grid = None
        self.bottom_toolbar = None
        self.bottom_toolbar_layout = None
        # Instância dos Botões
        self.min_button = None
        self.max_button = None
        self.close_button = None
        self.config_button = None
        self.folder_button = None
        self.start_button = None
        self.stop_button = None
        self.add_device_btn = None
        # Instância Label
        self.mic_logo_label = None
        self.program_version_label = None

        self.setWindowTitle("PyModbus Tester")
        self.window_size = QRect(0, 0, 900, 600)
        self.maximizado = True
        QTimer.singleShot(0, self.showMaximized)
        theme = custom_theme()
        self.setStyleSheet(theme)

        self.device_status_indicators = {}  # Dicionario para guardar o Status Indicator de cada Device
        self.runtime.device_state_changed.connect(self.update_device_status)

        # Remove bordas e barra de título
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self._posicao_click = QPoint()  # Variável para guardar posição do mouse ao clicar

        # App Layout
        self.app_layout = QVBoxLayout(self)
        self.app_layout.setContentsMargins(0, 0, 0, 0)
        self.app_layout.setSpacing(0)

        # Barra de Tarefas Superior
        self.create_top_toolbar()

        # Devices Frame
        self.create_devices_frame()

        # Barra de Tarefas Inferior
        self.create_bottom_toolbar()


    #------Criação da Interface-------

    def create_top_toolbar(self):
        self.top_toolbar = QFrame()
        self.top_toolbar.setFixedHeight(40)

        self.top_toolbar.installEventFilter(self) # Janela (self) vai monitorar os eventos de top_toolbar

        self.top_toolbar_layout = QHBoxLayout(self.top_toolbar)
        self.top_toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self.top_toolbar_layout.addStretch()
        self.top_toolbar_layout.setSpacing(20)

        self.app_layout.addWidget(self.top_toolbar)

        container3 = QWidget()
        container3.setFixedHeight(40)
        container3_layout = QHBoxLayout(container3)
        container3_layout.setContentsMargins(10, 0, 10, 0)
        container3_layout.addStretch()
        container3_layout.setSpacing(15)
        self.top_toolbar_layout.addWidget(container3, alignment=Qt.AlignLeft)

        self.mic_logo_label = QLabel()
        self.mic_logo_label.setPixmap(
            QPixmap(resource_path("icons", "logo.svg")).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        container3_layout.addWidget(self.mic_logo_label)

        self.top_toolbar_layout.addStretch(1)

        container1 = QWidget()
        container1.setFixedHeight(40)
        container1_layout = QHBoxLayout(container1)
        container1_layout.setContentsMargins(0, 0, 0, 0)
        container1_layout.addStretch()
        container1_layout.setSpacing(15)
        self.top_toolbar_layout.addWidget(container1, alignment=Qt.AlignLeft)

        self.start_button = self.create_button(self.start_button, container1_layout,
                                               icon_path=resource_path("icons", "start.svg"),
                                               icon_h=25, icon_w=25,
                                               tooltip="Começar Leitura",
                                               icon_color="#66cc67")

        self.stop_button = self.create_button(self.stop_button, container1_layout,
                                              icon_path=resource_path("icons", "stop.svg"),
                                              icon_h=20, icon_w=20,
                                              tooltip="Parar Leitura")

        self.folder_button = self.create_button(self.folder_button, container1_layout,
                                                icon_path=resource_path("icons", "folder.svg"),
                                                tooltip="Logs de Leitura")

        self.config_button = self.create_button(self.config_button, container1_layout,
                                                icon_path=resource_path("icons", "config.svg"),
                                                tooltip="Configurações")

        self.folder_button.clicked.connect(lambda: open_directory('/Desktop/LeiturasPyModbusTester'))
        self.config_button.clicked.connect(self.open_configWindow)

        self.start_button.clicked.connect(self.start_read)
        self.stop_button.clicked.connect(self.stop_read)

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)


        container2 = QWidget()
        container2.setFixedHeight(40)
        container2_layout = QHBoxLayout(container2)
        container2_layout.setContentsMargins(0, 0, 0, 0)
        container2_layout.addStretch()
        container2_layout.setSpacing(0)
        self.top_toolbar_layout.addWidget(container2, alignment=Qt.AlignLeft)

        self.close_button = QPushButton("✕")
        self.max_button = QPushButton("🗗")
        self.min_button = QPushButton("−")

        self.close_button.setObjectName("CloseButton")

        self.min_button.clicked.connect(self.showMinimized)
        self.max_button.clicked.connect(self.toggle_max_restore)
        self.close_button.clicked.connect(self.close)


        for btn in [self.min_button, self.max_button, self.close_button]:
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("margin: 0; border-radius: 0px; padding: 0; font-size: 14pt; font-weight: normal;")
            container2_layout.addWidget(btn, alignment=Qt.AlignLeft)



    def create_devices_frame(self):
        self.devices_frame = QFrame()
        self.devices_frame.setObjectName("DeviceFrame")

        self.devices_frame_layout = QHBoxLayout(self.devices_frame)

        self.app_layout.addWidget(self.devices_frame)

        #Área de Scroll
        self.scroll_device_frame = QScrollArea()
        self.scroll_device_frame.setWidgetResizable(True)
        self.scroll_device_frame.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_device_frame.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.devices_frame_layout.addWidget(self.scroll_device_frame)

        # Grid para os Devices
        self.device_grid_content = QWidget()
        self.device_grid_content.setObjectName("DeviceGrid")

        self.devices_grid = QGridLayout(self.device_grid_content)
        #self.devices_grid.setAlignment(Qt.AlignTop)  # Mantém os devices grudados no topo
        self.devices_grid.setHorizontalSpacing(15)
        self.devices_grid.setVerticalSpacing(15)
        self.scroll_device_frame.setWidget(self.device_grid_content)

        self.render_devices()

    def render_devices(self):
        while self.devices_grid.count():
            item = self.devices_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        max_por_linha = 5
        row = 0
        col = 0

        for dev_id, device in self.devices.items():
            frame = self.create_device_widget(dev_id)
            self.devices_grid.addWidget(frame, row, col)

            col += 1
            if col >= max_por_linha:
                col = 0
                row += 1

        self.add_device_btn = QPushButton()
        self.add_device_btn.setFixedSize(150, 60)
        self.add_device_btn.setIcon(QIcon(resource_path("icons", "add_device1.svg")))
        self.add_device_btn.setIconSize(QSize(50, 50))
        self.add_device_btn.setToolTip("Adicionar Dispositivo")

        self.devices_grid.addWidget(self.add_device_btn, row, col)
        self.add_device_btn.clicked.connect(self.add_device)


    def create_device_widget(self, dev_id):
        device = self.devices[dev_id]

        frame = QFrame()
        frame.setObjectName("DeviceWidgetFrame")
        frame.setFixedSize(150, 200)

        layout = QVBoxLayout(frame)

        header_frame = QFrame()
        header_frame_layout = QHBoxLayout(header_frame)
        header_frame_layout.setSpacing(0)
        header_frame_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(header_frame)

        status_indicator = StatusIndicator()
        header_frame_layout.addWidget(status_indicator)
        self.device_status_indicators[dev_id] = status_indicator

        num_lbl = QLabel(f"Device {dev_id}")
        header_frame_layout.addWidget(num_lbl, alignment=Qt.AlignCenter)

        #layout.addWidget(num_lbl)

        if device.nome:
            name_lbl = QLabel(device.nome)
            name_lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(name_lbl)

        device_config_btn = self.create_button(
            None, layout,
            icon_path=resource_path("images", "device_icon.png"),
            icon_h=60, icon_w=60,
            tooltip="Configurações do Device",
            btn_h=60, btn_w=60,
            btn_alignment=Qt.AlignCenter
        )

        device_config_btn.clicked.connect(
            lambda _, d=device: self.open_deviceConfigWindow(d)
        )

        line = QFrame()
        line.setFixedHeight(2)
        line.setObjectName("LineFrame")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        btn_frame = QFrame()
        btn_frame_layout = QHBoxLayout(btn_frame)
        btn_frame_layout.setSpacing(10)
        layout.addWidget(btn_frame)

        btn_frame_layout.addStretch()

        btn_openDeviceMonitorWindow = self.create_button(
            None, btn_frame_layout,
            icon_path=resource_path("icons", "glass_icon.svg"),
            icon_h=25, icon_w=25,
            tooltip="Visualizar Registros",
            btn_h=30, btn_w=30,
            btn_alignment=Qt.AlignCenter
        )
        btn_openDeviceMonitorWindow.setObjectName("ViewRegistersButton")
        btn_openDeviceMonitorWindow.clicked.connect(lambda _, d=dev_id: self.open_deviceMonitorWindow(self.devices[d]))

        btn_del = self.create_button(
            None, btn_frame_layout,
            icon_path=resource_path("icons", "delete.svg"),
            icon_h=25, icon_w=25,
            tooltip="Remover Device",
            btn_h=30, btn_w=30,
            btn_alignment=Qt.AlignCenter
        )
        btn_del.setObjectName("RemoveDeviceButton")
        btn_del.clicked.connect(lambda _, d=dev_id: self.remove_device(d))

        btn_frame_layout.addStretch()

        return frame

    def add_device(self):
        novo_id = str(len(self.devices) + 1)
        self.devices[novo_id] = Device(novo_id)

        save_devices(self.devices)
        self.render_devices()

    def remove_device(self, dev_id):
        if dev_id in self.devices:
            del self.devices[dev_id]

        novos = {}
        for i, key in enumerate(sorted(self.devices.keys(), key=lambda x: int(x)), start=1):
            novos[str(i)] = self.devices[key]

        self.devices = novos

        save_devices(self.devices)
        self.render_devices()

    def update_device_status(self, device, status):
        indicator = self.device_status_indicators.get(device.dev_id)

        if indicator:
            indicator.set_status(status)
            indicator.set_tooltip(status)

    def create_bottom_toolbar(self):
        self.bottom_toolbar = QFrame()
        self.bottom_toolbar.setFixedHeight(40)
        self.bottom_toolbar_layout = QHBoxLayout(self.bottom_toolbar)
        self.app_layout.addWidget(self.bottom_toolbar)

        container1 = QWidget()
        container1.setFixedHeight(40)
        container1_layout = QHBoxLayout(container1)
        container1_layout.setContentsMargins(0, 0, 0, 15)
        container1_layout.addStretch()
        container1_layout.setSpacing(0)
        self.bottom_toolbar_layout.addWidget(container1, alignment=Qt.AlignRight)

        self.console_button = self.create_button(None, container1_layout,
                                                 icon_path=resource_path("icons", "console.svg"),
                                                 tooltip="Console",
                                                 btn_alignment=Qt.AlignRight)
        self.console_button.clicked.connect(self.open_consoleWindow)

        self.bottom_toolbar_layout.addStretch(1)

        container2 = QWidget()
        container2.setFixedHeight(40)
        container2_layout = QHBoxLayout(container2)
        container2_layout.setContentsMargins(0, 0, 0, 15)
        container2_layout.addStretch()
        container2_layout.setSpacing(0)
        self.bottom_toolbar_layout.addWidget(container2, alignment=Qt.AlignRight)

        self.program_version_label = QLabel('PyModbus Tester - v' + self.program_version)
        container2_layout.addWidget(self.program_version_label)


    def create_button(self, button, layout, label="", btn_h=30, btn_w=30, btn_alignment=Qt.AlignRight,
                      icon_path="", icon_h=25, icon_w=25, icon_color="#D1D1D1", tooltip=""):
        if button is None:
            button = QPushButton(label)
        button.setFixedSize(btn_h, btn_w)
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(icon_h, icon_w))
        if tooltip:
            button.setToolTip(tooltip)
        layout.addWidget(button, alignment=btn_alignment)
        return button


    #------Funções para Interface-------

    def toggle_max_restore(self):
        if self.maximizado:
            self.showNormal()
            QTimer.singleShot(10, lambda: self.setGeometry(self.window_size))
            self.maximizado = False
            self.max_button.setText("🗖")
        else:
            self.showMaximized()
            self.maximizado = True
            self.max_button.setText("🗗")


    # Metodo que intercepta eventos do widget

    def eventFilter(self, source, event):
        if source == self.top_toolbar:
            if not self.maximizado:
                if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                    self._posicao_click = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                    return True
                elif event.type() == QEvent.MouseMove and event.buttons() & Qt.LeftButton:
                    self.move(event.globalPosition().toPoint() - self._posicao_click)
                    return True
        return super().eventFilter(source, event)

    # -------Funções de Abrir Guias --------

    def open_configWindow(self):
        self.config_window = ConfigWindow(self.program_settings)
        self.config_window.exec()

    def open_deviceConfigWindow(self, device):
        self.device_config_window = DeviceConfigWindow(device)
        self.device_config_window.exec()

        save_devices(self.devices)
        self.render_devices()

    def open_deviceMonitorWindow(self, device):
        self.device_monitor_window = DeviceMonitorWindow(device, self.runtime)
        self.device_monitor_window.exec()

    def open_consoleWindow(self):
        self.console_window = None
        if not hasattr(self, "console_window") or self.console_window is None:
            self.console_window = ConsoleWindow()
        self.console_window.show()
        self.console_window.raise_()

    # -------Funções Auxiliares-------

    def start_read(self):
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        settings = load_program_settings()
        devices = load_devices()

        self.runtime.update_context(
            devices=devices,
            interval=settings.intervalo_de_leitura,
            timeout=settings.timeout
        )

        self.runtime.start()

    def stop_read(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        asyncio.create_task(self.runtime.stop())

    # ------Fechamento App--------

    def closeEvent(self, event):
        save_program_settings(self.program_settings.to_dict())
        save_devices(self.devices)

        if self.runtime:
            try:
                loop = self.runtime._task.get_loop()
                loop.create_task(self.runtime.stop())
            except Exception:
                pass

        event.accept()









