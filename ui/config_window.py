from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QLineEdit, QComboBox, QStackedWidget, \
    QTreeView, QMessageBox

from core.utils import resource_path
from models.device import Device
from models.program_settings import ProgramSettings
from models.registers import RegisterConfig
from ui.base_window import BaseWindow


class ConfigWindow(BaseWindow):
    def __init__(self, program_settings: ProgramSettings):
        super().__init__(400, 300, "Configurações de Leitura")

        # Instancias
        self.configs_frame = None
        self.configs_frame_layout = None

        self.program_settings = program_settings

        # Cria os campos de configuração
        self.create_fields()

    def create_fields(self):
        self.configs_frame = QFrame()
        self.configs_frame.setObjectName("BgWindowFrame")

        self.configs_frame_layout = QVBoxLayout(self.configs_frame)
        self.configs_frame_layout.setContentsMargins(20, 0, 0, 0)
        self.configs_frame_layout.setSpacing(20)

        self.window_layout.addWidget(self.configs_frame)

        # Mapeamento
        fields = {
            "Máx. Leituras Por Arquivo": "max_read_per_file",
            "Intervalo de Leitura (s)": "intervalo_de_leitura",
            "Timeout (ms)": "timeout",
        }

        for label_text, attr_name in fields.items():
            container = QWidget()
            container.setFixedHeight(40)
            container.setStyleSheet("background-color: transparent")

            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 15)
            container_layout.addStretch()
            container_layout.setSpacing(0)

            self.configs_frame_layout.addWidget(container, alignment=Qt.AlignLeft)

            label = QLabel(label_text + ": ")

            entry = QLineEdit()
            entry.setText(str(getattr(self.program_settings, attr_name)))

            # ligação UI → Model
            entry.textChanged.connect(
                lambda text, a=attr_name: self.update_setting(a, text)
            )

            container_layout.addWidget(label, alignment=Qt.AlignRight)
            container_layout.addWidget(entry, alignment=Qt.AlignRight)

    def update_setting(self, attr_name, value):
        if attr_name in ("timeout", "intervalo_de_leitura", "max_read_per_file"):
            if not value.isdigit():
                return
            value = int(value)

        setattr(self.program_settings, attr_name, value)

    def closeWindow(self):

        self.close()

class DeviceConfigWindow(BaseWindow):
    def __init__(self, device: Device):
        super().__init__(700, 500, "Configurações do Device")

        self.device = device
        self.create_fields()
        self.device.registers_changed.connect(self.refresh_tree)


    def create_fields(self):
        self.configs_frame = QFrame()
        self.configs_frame.setObjectName("BgWindowFrame")

        self.configs_frame_layout = QVBoxLayout(self.configs_frame)
        self.window_layout.addWidget(self.configs_frame)

        self.tipo_conexao_container = QWidget()
        #self.tipo_conexao_container.setFixedHeight(40)
        self.tipo_conexao_container.setObjectName("TransparentWidget")

        self.tipo_conexao_container_layout = QHBoxLayout(self.tipo_conexao_container)
        self.tipo_conexao_container_layout.setContentsMargins(0, 0, 0, 15)
        self.tipo_conexao_container_layout.addStretch()
        self.tipo_conexao_container_layout.setSpacing(10)

        self.configs_frame_layout.addWidget(self.tipo_conexao_container, alignment=Qt.AlignLeft)

        self.tipo_conexao_label = QLabel("Tipo de Conexão: ")
        self.tipo_conexao_label.setObjectName("TransparentLabel")
        self.tipo_conexao_combo = QComboBox()
        self.tipo_conexao_combo.addItem("Modbus TCP", "tcp")
        self.tipo_conexao_combo.addItem("Modbus RTU", "rtu")
        self.tipo_conexao_combo.setCurrentIndex(
            self.tipo_conexao_combo.findData(self.device.tipo_conexao)
        )

        self.tipo_conexao_container_layout.addWidget(self.tipo_conexao_label, alignment=Qt.AlignLeft)
        self.tipo_conexao_container_layout.addWidget(self.tipo_conexao_combo, alignment=Qt.AlignLeft)

        self.main_content = QFrame()
        self.main_content_layout = QHBoxLayout(self.main_content)
        self.main_content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_content_layout.setSpacing(10)

        self.configs_frame_layout.addWidget(self.main_content)

        self.stacked_pages = QStackedWidget()
        self.main_content_layout.addWidget(self.stacked_pages, alignment=Qt.AlignLeft)

        self.page_tcp = self.create_tcp_page()
        self.page_rtu = self.create_rtu_page()

        self.stacked_pages.addWidget(self.page_tcp)
        self.stacked_pages.addWidget(self.page_rtu)

        self.tipo_conexao_combo.currentIndexChanged.connect(self.on_tipo_changed)

        self.tipo_conexao_combo.currentIndexChanged.connect(
            lambda _, a= "tipo_conexao", c= self.tipo_conexao_combo: self.update_setting(a, c.currentData())
        )

        self.tipo_conexao_combo.setCurrentIndex(self.tipo_conexao_combo.findData(self.device.tipo_conexao))

        self.on_tipo_changed()

        self.create_reg_field()


    def create_tcp_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)

        # Mapeamento
        fields = {
            "Nome do Dispositivo": "nome",
            "Endereço IP": "ip",
            "Porta": "porta",
            "Endereço do Device": "endereco",
            "Habilitado": "enabled",
            "Habilitar Log": "log_enabled"
        }
        option_menu_fields = ["enabled", "log_enabled"]

        for label_text, attr_name in fields.items():
            container = QWidget()
            container.setFixedHeight(40)
            container.setObjectName("TransparentWidget")

            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 15)
            container_layout.addStretch()
            container_layout.setSpacing(10)

            #self.configs_frame_layout.addWidget(container, alignment=Qt.AlignLeft)
            page_layout.addWidget(container, alignment=Qt.AlignLeft)

            label = QLabel(label_text + ": ")


            if attr_name in option_menu_fields:
                entry = QComboBox()

                if attr_name == "enabled" or "log_enabled":
                    opcoes = ["True", "False"]
                    entry.addItems(opcoes)

                entry.setCurrentText(str(getattr(self.device, attr_name)))
                entry.currentIndexChanged.connect(
                    lambda _, a=attr_name, c=entry: self.update_setting(a, c.currentText())
                )

            else:
                entry = QLineEdit()
                entry.setText(str(getattr(self.device, attr_name)))

                # ligação UI → Model
                entry.textChanged.connect(
                    lambda text, a=attr_name: self.update_setting(a, text)
                )


            container_layout.addWidget(label, alignment=Qt.AlignRight)
            container_layout.addWidget(entry, alignment=Qt.AlignRight)

        return page

    def create_rtu_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)

        # Mapeamento
        fields = {
            "Nome do Dispositivo": "nome",
            "Porta COM": "porta_com",
            "Baudrate": "baudrate",
            "Paridade": "paridade",
            "Bits de Parada": "bits_parada",
            "Tamanho do Byte": "tamanho_byte",
            "Endereço do Device": "endereco",
            "Habilitado": "enabled",
            "Habilitar Log": "log_enabled"
        }
        option_menu_fields = ["baudrate", "paridade", "enabled", "log_enabled"]

        for label_text, attr_name in fields.items():
            container = QWidget()
            container.setFixedHeight(40)
            container.setObjectName("TransparentWidget")

            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 15)
            container_layout.addStretch()
            container_layout.setSpacing(10)

            #self.configs_frame_layout.addWidget(container, alignment=Qt.AlignLeft)
            page_layout.addWidget(container, alignment=Qt.AlignLeft)

            label = QLabel(label_text + ": ")

            if attr_name in option_menu_fields:
                entry = QComboBox()

                if attr_name == "baudrate":
                    opcoes = ["9600", "19200", "38400", "115200"]
                    entry.addItems(opcoes)

                elif attr_name == "paridade":
                    opcoes = ["N", "E", "O"]
                    entry.addItems(opcoes)

                elif attr_name == "enabled" or "log_enabled":
                    opcoes = ["True", "False"]
                    entry.addItems(opcoes)

                entry.setCurrentText(str(getattr(self.device, attr_name)))
                entry.currentIndexChanged.connect(
                    lambda _, a=attr_name, c=entry: self.update_setting(a, c.currentText())
                )

            else:
                entry = QLineEdit()
                entry.setText(str(getattr(self.device, attr_name)))

                # ligação UI → Model
                entry.textChanged.connect(
                    lambda text, a=attr_name: self.update_setting(a, text)
                )

            container_layout.addWidget(label, alignment=Qt.AlignRight)
            container_layout.addWidget(entry, alignment=Qt.AlignRight)

        return page

    def on_tipo_changed(self):
        tipo = self.tipo_conexao_combo.currentData()

        if tipo == "tcp":
            self.stacked_pages.setCurrentWidget(self.page_tcp)
        elif tipo == "rtu":
            self.stacked_pages.setCurrentWidget(self.page_rtu)


    def create_reg_field(self):
        self.tree_container = QFrame()
        self.tree_layout = QHBoxLayout(self.tree_container)
        self.tree_layout.setContentsMargins(0, 0, 0, 0)
        self.tree_layout.setSpacing(6)

        self.tree = QTreeView(self)
        self.tree_layout.addWidget(self.tree)

        self.main_content_layout.addWidget(self.tree_container, 1)

        self.model = QStandardItemModel()
        self.tree.setModel(self.model)

        self.tree.setHeaderHidden(False)
        self.tree.setExpandsOnDoubleClick(True)

        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)  # se for hierárquica
        self.tree.setIndentation(20)

        self.refresh_tree()
        self.tree.doubleClicked.connect(self.on_tree_doubleClicked)

        self.tree_buttons = QWidget()
        self.tree_buttons_layout = QVBoxLayout(self.tree_buttons)
        self.tree_buttons_layout.setContentsMargins(0, 0, 5, 0)
        self.tree_buttons_layout.setSpacing(8)
        self.tree_layout.addWidget(self.tree_buttons)

        self.tree_buttons_layout.addStretch()

        self.add_reg_btn = self.create_button(None, self.tree_buttons_layout,
                                              icon_path=resource_path("icons", "add_device.svg"),
                                              icon_h=25, icon_w=25, tooltip="Adicionar Registro",
                                              btn_alignment=Qt.AlignRight)
        self.add_reg_btn.clicked.connect(self.openAddRegisterWindow)

        self.remove_reg_btn = self.create_button(None, self.tree_buttons_layout,
                                                 icon_path=resource_path("icons", "delete.svg"),
                                                 icon_h=25, icon_w=25, tooltip="Remover Registro",
                                                 btn_alignment=Qt.AlignRight)
        self.remove_reg_btn.clicked.connect(self.on_remove_register)

        self.edit_reg_btn = self.create_button(None, self.tree_buttons_layout,
                                               icon_path=resource_path("icons", "edit.svg"),
                                               icon_h=25, icon_w=25, tooltip="Editar Registro",
                                               btn_alignment=Qt.AlignRight)
        self.edit_reg_btn.clicked.connect(self.on_edit_register)

        self.tree_buttons_layout.addStretch()

    def refresh_tree(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Registros Modbus"])

        # Mapeamento função → nome exibido
        func_map = {
            "holding": "Holding Registers",
            "input": "Input Registers",
            "coil": "Coils",
        }

        # Cria nós raiz por função
        func_items = {}
        for func, label in func_map.items():
            item = QStandardItem(label)
            item.setEditable(False)
            self.model.appendRow(item)
            func_items[func] = item

        # Adiciona registros
        for reg in self.device.registros:
            func_item = func_items.get(reg.funcao)
            if not func_item:
                continue

            text = f"{reg.endereco} - {reg.nome}"
            reg_item = QStandardItem(text)
            reg_item.setEditable(False)

            # Guarda o objeto RegisterConfig
            reg_item.setData(reg, Qt.UserRole)

            func_item.appendRow(reg_item)

        self.expand_root_items()

    def expand_root_items(self):
        for row in range(self.model.rowCount()):
            index = self.model.index(row, 0, QModelIndex())
            self.tree.expand(index)

    def get_selected_register(self):
        index = self.tree.currentIndex()

        if not index.isValid():
            return None

        item: QStandardItem = self.model.itemFromIndex(index)
        if not item:
            return None

        reg = item.data(Qt.UserRole)
        return reg

    def on_tree_doubleClicked(self, index):
        item = self.model.itemFromIndex(index)

        registro = item.data(Qt.UserRole)
        if registro:
            self.openEditRegisterWindow(registro)

    def on_remove_register(self):
        reg = self.get_selected_register()

        if not reg:
            QMessageBox.warning(
                self,
                "Nenhum registro selecionado",
                "Selecione um registro para remover."
            )
            return

        self.device.registros.remove(reg)
        self.device.registers_changed.emit()

    def on_edit_register(self):
        reg = self.get_selected_register()

        if not reg:
            QMessageBox.warning(
                self,
                "Nenhum registro selecionado",
                "Selecione um registro para editar."
            )
            return

        self.openEditRegisterWindow(reg)

    def openAddRegisterWindow(self):
        self.add_register_config_window = RegisterConfigWindow(device=self.device)
        self.add_register_config_window.exec()

    def openEditRegisterWindow(self, registro):
        self.edit_register_config_window = RegisterConfigWindow(device=self.device, registro=registro)
        self.edit_register_config_window.exec()

    def update_setting(self, attr_name, value):
        """
        if attr_name in ("timeout", "intervalo_de_leitura", "max_read_per_file"):
            if not value.isdigit():
                return
            value = int(value)
        """
        setattr(self.device, attr_name, value)

        #self.configs_frame_layout.addWidget(container)

    def closeWindow(self):
        self.close()

class RegisterConfigWindow(BaseWindow):
    def __init__(self, device, registro=None):
        super().__init__(350, 700, "Configurar Registro")

        self.device = device

        if registro is None:
            self.registro = RegisterConfig()
            self.modo = "novo"
        else:
            self.registro = registro
            self.modo = "editar"

        self.create_fields()

    def create_fields(self):
        self.configs_frame = QFrame()
        self.configs_frame.setObjectName("BgWindowFrame")

        self.configs_frame_layout = QVBoxLayout(self.configs_frame)
        self.window_layout.addWidget(self.configs_frame)
        page = QWidget()
        page_layout = QVBoxLayout(page)

        # Mapeamento
        fields = {
            "ID do Registro": "id",
            "Nome do Registro": "nome",
            "Função": "funcao",
            "Endereço do Registro": "endereco",
            "Quantidade": "quantidade",
            "Modo de Leitura": "modo_leitura",
            "Datatype": "datatype",
            "Divisor": "divisor",
            "Offset": "offset",
            "Formula": "formula",
            "Unidade de Medida": "unidade_medida",
            "Byte Order": "byte_order",
            "Word Order": "word_order",
            "Signed": "signed",
            "Valor Minímo": "min_value",
            "Valor Máximo": "max_value",
            "Habilitado": "enabled"

        }
        self.option_menu_fields = ["funcao", "modo_leitura", "datatype", "byte_order", "word_order", "signed", "enabled"]
        self.entry_list = {}

        for label_text, attr_name in fields.items():
            container = QWidget()
            container.setFixedHeight(40)
            container.setObjectName("TransparentWidget")

            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 15)
            container_layout.addStretch()
            container_layout.setSpacing(10)

            page_layout.addWidget(container, alignment=Qt.AlignLeft)

            label = QLabel(label_text + ": ")

            if attr_name in self.option_menu_fields:
                entry = QComboBox()

                if attr_name == "funcao":
                    opcoes = ["holding", "input", "coil"]
                    entry.addItems(opcoes)

                elif attr_name == "modo_leitura":
                    opcoes = ["SINGLE", "BLOCK", "AUTO"]
                    entry.addItems(opcoes)

                elif attr_name == "datatype":
                    opcoes = ["UINT16", "INT16", "UINT32", "INT32", "FLOAT32"]
                    entry.addItems(opcoes)

                elif attr_name == "byte_order":
                    opcoes = ["BIG", "LITTLE"]
                    entry.addItems(opcoes)

                elif attr_name == "word_order":
                    opcoes = ["BIG", "LITTLE"]
                    entry.addItems(opcoes)

                elif attr_name == "signed":
                    opcoes = ["true", "false"]
                    entry.addItems(opcoes)

                elif attr_name == "enabled":
                    opcoes = ["True", "False"]
                    entry.addItems(opcoes)

                entry.setCurrentText(str(getattr(self.registro, attr_name)))

            else:
                entry = QLineEdit()
                entry.setText(str(getattr(self.registro, attr_name)))

            self.entry_list[attr_name] = entry
            container_layout.addWidget(label, alignment=Qt.AlignRight)
            container_layout.addWidget(entry, alignment=Qt.AlignRight)

        self.configs_frame_layout.addWidget(page, alignment=Qt.AlignLeft)

    def save(self):
        try:
            for attr_name, entry in self.entry_list.items():
                if attr_name in self.option_menu_fields:
                    setattr(self.registro, attr_name, entry.currentText())
                else:
                    setattr(self.registro, attr_name, entry.text())

            #Add ou faz um update nos registros, e se existir repetidos, add em skipped para exibir posteriormente
            if self.modo == "novo":
                skipped = self.device.add_register(self.registro)
            else:
                skipped = self.device.update_register(self.registro)

            if skipped:
                QMessageBox.warning(
                    self,
                    "Registros Duplicados Detectados",
                    f"Os seguintes endereços já existiam e foram ignorados:\n{', '.join(skipped)}"
                )

        except Exception as e:
            print("Erro ao salvar:", e)
            # aqui você pode mostrar QMessageBox

    def closeWindow(self):
        self.save()
        self.close()
