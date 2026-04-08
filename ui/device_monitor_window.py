from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTableView
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor

from modbus.reading import Reading
from models.device import Device
from ui.base_window import BaseWindow


class DeviceMonitorWindow(BaseWindow):
    def __init__(self, device: Device, runtime):
        super().__init__(900, 700, f"Monitor de Registros - Device {device.dev_id}")

        self.device = runtime.devices[device.dev_id]
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

        self.device.registers_changed.connect(self.on_registers_changed)

        # -------------------------
        # Runtime updates
        # -------------------------

    def on_registers_changed(self):
        self.model.refresh()
    ''''
    def on_value_updated(self, device, reg_addr):
        print("UI recebeu update")
        # Garantia de identidade correta
        if device.dev_id != self.device.dev_id:
            return

        reg_addr = int(reg_addr)

        self.model.update_register(reg_addr)
        self.table.viewport().update()
    '''

    def on_value_updated(self, reading: Reading):
        print("UI recebeu update")
        # Garantia de identidade correta
        if reading.device_id != self.device.dev_id:
            return

        reg_addr = int(reading.address)

        self.model.update_register(reg_addr)
        self.table.viewport().update()

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

        elif state == "CONNECTING":
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
        self.runtime = runtime
        self.registers = device.registros

        self._row_map = {
            reg.endereco: i
            for i, reg in enumerate(self.registers)
        }

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
                print("VALUE DEBUG:", reg.endereco, reg.last_value)
                if reg.last_error:
                    return f"Erro: {reg.last_error}"

                if reg.last_value is None:
                    return "—"

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

        if role == Qt.BackgroundRole and col == 7:

            state = self.runtime.device_states.get(self.device.dev_id)

            if state == "OFFLINE":
                return QColor("#3a1f1f")

            if reg.last_error:
                return QColor("#4a1f1f")

            if reg.last_value is not None:
                return QColor("#1f3a1f")

        # -------- Cor do texto --------
        if role == Qt.ForegroundRole:
            if reg.last_error:
                return QColor("#ff6b6b")

        return None

    # -------------------------
    # Atualização por registro
    # -------------------------

    def update_register(self, address):

        row = self._row_map.get(address)

        if row is None:
            return

        top_left = self.index(row, 4)
        bottom_right = self.index(row, 7)

        self.dataChanged.emit(
            top_left,
            bottom_right,
            [Qt.DisplayRole, Qt.BackgroundRole]
        )

    def refresh(self):
        self.beginResetModel()

        self.registers = self.device.registros

        self._row_map = {
            reg.endereco: i
            for i, reg in enumerate(self.registers)
        }

        self.endResetModel()