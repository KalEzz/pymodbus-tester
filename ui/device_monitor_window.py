from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTableView
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor

from models.device import Device
from ui.base_window import BaseWindow


class DeviceMonitorWindow(BaseWindow):
    def __init__(self, device: Device, runtime):
        super().__init__(900, 300, f"Monitor de Registros - Device {device.dev_id}")

        self.device = device
        self.runtime = runtime

        # Cria os campos
        self.create_fields()
        self._connect_signals()

        self._sync_initial_state()

    def create_fields(self):
        self.main_frame = QFrame()
        self.main_frame.setObjectName("BgWindowFrame")

        self.main_frame_layout = QVBoxLayout(self.main_frame)
        self.window_layout.addWidget(self.main_frame)

        # ---- Header ----
        header_layout = QHBoxLayout()

        self.device_label = QLabel(
            f"Device {self.device.dev_id} - {self.device.nome}"
        )
        self.device_label.setAlignment(Qt.AlignLeft)

        self.state_label = QLabel("STOPPED")
        self.state_label.setAlignment(Qt.AlignRight)

        header_layout.addWidget(self.device_label)
        header_layout.addWidget(self.state_label)

        self.main_frame_layout.addLayout(header_layout)

        # ---- Table ----
        self.model = DeviceRegisterTableModel(self.device, self.runtime)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSortingEnabled(False)

        self.table.horizontalHeader().setStretchLastSection(True)

        self.main_frame_layout.addWidget(self.table)

        # -------------------------
        # Signals
        # -------------------------

    def _sync_initial_state(self):
        state = self.runtime.device_states.get(
            self.device.dev_id,
            "STOPPED"
        )
        self._update_state_label(state)

    def _connect_signals(self):
        self.runtime.value_updated.connect(
            self.on_value_updated,
            Qt.QueuedConnection
        )
        self.runtime.device_state_changed.connect(
            self.on_device_state_changed,
            Qt.QueuedConnection
        )

        # -------------------------
        # Runtime updates
        # -------------------------

    def on_value_updated(self, device, result):
        print("UI recebeu update")
        # Garantia de identidade correta
        if device is not self.device:
            return

        reg = result.reg

        # Atualiza somente essa linha
        self.model.update_register(reg)

    def on_device_state_changed(self, device, state):
        print("UI recebeu estado:", device.dev_id, state)
        if device.dev_id != self.device.dev_id:
            return

        self._update_state_label(state)

        self.model.layoutChanged.emit()

    def _update_state_label(self, state):

        self.state_label.setText(state)

        # Cor visual por estado
        if state == "RUNNING":
            self.state_label.setStyleSheet("color: #00ff7f; font-weight: bold;")

        elif state == "OFFLINE":
            self.state_label.setStyleSheet("color: #ffcc00; font-weight: bold;")

        elif state == "RECONNECTING":
            self.state_label.setStyleSheet("color: #00bfff; font-weight: bold;")

        elif state == "ERROR":
            self.state_label.setStyleSheet("color: #ff4c4c; font-weight: bold;")

        else:
            self.state_label.setStyleSheet("color: white;")

    # -------------------------
    # Cleanup
    # -------------------------

    def closeWindow(self):
        try:
            self.runtime.value_updated.disconnect(self.on_value_updated)
            self.runtime.device_state_changed.disconnect(self.on_device_state_changed)
        except:
            pass

        self.close()

class DeviceRegisterTableModel(QAbstractTableModel):

    HEADERS = [
        "Address",
        "Name",
        "Function",
        "Type",
        "Value",
        "Unit",
        "Timestamp",
        "Status",
    ]

    def __init__(self, device, runtime):
        super().__init__()
        self.device = device
        self.registers = list(device.registros)
        self.runtime = runtime

        # Mapa rápido para achar linha em O(1)
        self.row_map = {reg.endereco: i for i, reg in enumerate(self.registers)}

    # -------------------------
    # Qt obrigatório
    # -------------------------

    def rowCount(self, parent=QModelIndex()):
        return len(self.registers)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None

    # -------------------------
    # Dados
    # -------------------------

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        reg = self.registers[index.row()]
        col = index.column()
        # -------- CheckBoxDisabled --------
        if role == Qt.CheckStateRole:
            return None

        # -------- Texto --------
        if role == Qt.DisplayRole:

            if col == 0:
                return reg.endereco
            elif col == 1:
                return reg.nome
            elif col == 2:
                return reg.funcao
            elif col == 3:
                return reg.datatype
            elif col == 4:

                state = self.runtime.device_states.get(self.device.dev_id)

                if state in ("OFFLINE", "STOPPED"):
                    return "—"

                if state == "CONNECTING" and reg.last_value is not None:
                    return f"{reg.last_value} (stale)"

                if reg.last_error:
                    return f"Erro: {reg.last_error}"

                return reg.last_value
            elif col == 5:
                return reg.unidade_medida
            elif col == 6:
                if reg.last_timestamp:
                    return reg.last_timestamp.strftime("%H:%M:%S")
                return ""
            elif col == 7:

                state = self.runtime.device_states.get(self.device.dev_id)

                if state == "OFFLINE":
                    return "OFFLINE"

                if state == "CONNECTING":
                    return "CONNECTING"

                if reg.last_error:
                    return "ERROR"

                if reg.last_value is None:
                    return "-"

                return "OK"

        # -------- Cor de fundo --------
        elif col == 7:

            state = self.runtime.device_states.get(self.device.dev_id)

            if state == "OFFLINE":
                return "OFFLINE"

            if state == "CONNECTING":
                return "CONNECTING"

            if reg.last_error:
                return "ERROR"

            if reg.last_value is None:
                return "-"

            return "OK"

        # -------- Cor do texto --------
        if role == Qt.ForegroundRole:
            if reg.last_error:
                return QColor("#ff6b6b")

        return None

    # -------------------------
    # Atualização por registro
    # -------------------------

    def update_register(self, reg):
        row = self.row_map.get(reg.endereco)
        if row is None:
            return

        left = self.index(row, 0)
        right = self.index(row, self.columnCount() - 1)

        self.dataChanged.emit(left, right, [
            Qt.DisplayRole,
            Qt.BackgroundRole,
            Qt.ForegroundRole
        ])