import asyncio
import copy

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QMessageBox
from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient

from core.utils import parse_address_ranges
from models.registers import RegisterConfig

class Device(QObject):
    registers_changed = Signal()
    state_changed = Signal(str)

    def __init__(self, dev_id: str):
        super().__init__()
        self.dev_id = dev_id

        self.tipo_conexao = "rtu"
        self.nome = ""
        self.timeout = 1

        #Controle
        self.enabled: str = "True"
        self.log_enabled: str = "True"

        #TCP
        self.ip = ""
        self.porta = "502"

        #RTU
        self.porta_com = "COM6"
        self.baudrate = "9600"
        self.paridade = "N"
        self.bits_parada = "1"
        self.tamanho_byte = "8"
        self.endereco = "1"
        self.registros: list[RegisterConfig] = []

    def get_register(self, endereco):
        for reg in self.registros:
            if str(reg.endereco) == str(endereco):
                return reg
        return None

    def add_register(self, registro: RegisterConfig):
        if not isinstance(registro, RegisterConfig):
            raise TypeError("registro precisa ser RegisterConfig")

        start, qty = parse_address_ranges(registro.endereco)

        skipped = []
        added_any = False

        if qty == 1:
            if self._exists(registro.endereco, registro.funcao):
                skipped.append(registro.endereco)
            else:
                self.registros.append(registro)
                added_any = True

        else:
            for offset in range(qty):
                addr = str(start + offset)

                if self._exists(addr, registro.funcao):
                    skipped.append(addr)
                    continue

                new_reg = copy.deepcopy(registro)
                new_reg.endereco = addr

                self.registros.append(new_reg)
                added_any = True

        if added_any:
            self.registers_changed.emit()

        return skipped

    def _exists(self, endereco, funcao):
        for reg in self.registros:
            if reg.endereco == endereco and reg.funcao == funcao:
                return True
        return False

    def _add_single_register(self, registro):
        # regra de duplicidade
        for reg in self.registros:
            if reg.endereco == registro.endereco and reg.funcao == registro.funcao:
                raise ValueError("Já existe registro com esse endereço e função")

        self.registros.append(registro)

    def remove_register(self, reg: RegisterConfig):
        if reg in self.registros:
            self.registros.remove(reg)
            self.registers_changed.emit()

    def update_register(self, reg: RegisterConfig):

        # Verifica se o registro está na lista
        if reg not in self.registros:
            raise ValueError("Registro não encontrado no device")

        # Se endereço virou faixa (ex: 5-7)
        if "-" in str(reg.endereco):

            # Remove o registro atual
            self.registros.remove(reg)

            # Reinsere usando add_register (expande corretamente)
            try:
                self.add_register(reg)
            except Exception as e:
                # Se falhar, restaura original
                self.registros.append(reg)
                raise e

        else:
            # Valida duplicidade simples
            for other in self.registros:
                if (
                        other is not reg and
                        other.endereco == reg.endereco and
                        other.funcao == reg.funcao
                ):
                    raise ValueError("Já existe registro com esse endereço e função")

            self.registers_changed.emit()

    def clear_registers(self):
        self.registros.clear()
        self.registers_changed.emit()

    async def create_client(self, timeout):
        if self.tipo_conexao == "tcp":
            client = AsyncModbusTcpClient(
                host=self.ip,
                port=int(self.porta),
                timeout=timeout
            )

        elif self.tipo_conexao == "rtu":
            client = AsyncModbusSerialClient(
                port=self.porta_com,
                baudrate=int(self.baudrate),
                parity=self.paridade,
                stopbits=int(self.bits_parada),
                bytesize=int(self.tamanho_byte),
                timeout=timeout
            )

        # 🔥 TIMEOUT NO CONNECT
        try:
            await asyncio.wait_for(client.connect(), timeout=timeout + 0.5)
        except asyncio.TimeoutError:
            raise ConnectionError("Timeout ao abrir porta serial")

        if not client.connected:
            raise ConnectionError(f"Falha ao conectar {self.nome}")

        return client

    # ---- Conversão para JSON ----
    def to_dict(self):
        return {
            "tipo_conexao": self.tipo_conexao,
            "nome": self.nome,
            "ip": self.ip,
            "enabled": self.enabled,
            "log_enabled": self.log_enabled,
            "porta": self.porta,
            "porta_com": self.porta_com,
            "baudrate": self.baudrate,
            "paridade": self.paridade,
            "bits_parada": self.bits_parada,
            "tamanho_byte": self.tamanho_byte,
            "endereco": self.endereco,
            "registros": [reg.to_dict() for reg in self.registros]
        }

    # ---- Criar objeto a partir de JSON ----
    @classmethod
    def from_dict(cls, dev_id, data):
        dev = cls(dev_id)

        dev.tipo_conexao = data.get("tipo_conexao", "rtu")
        dev.nome = data.get("nome", "")
        dev.ip = data.get("ip", "")
        dev.enabled = data.get("enabled", "True")
        dev.log_enabled = data.get("log_enabled", "True")
        dev.porta = data.get("porta", "502")
        dev.porta_com = data.get("porta_com", "COM6")
        dev.baudrate = data.get("baudrate", "9600")
        dev.paridade = data.get("paridade", "N")
        dev.bits_parada = data.get("bits_parada", "1")
        dev.tamanho_byte = data.get("tamanho_Byte", "8")
        dev.endereco = data.get("endereco", "1")
        dev.registros = []

        registros_data = data.get("registros", [])

        for reg_data in registros_data:
            reg = RegisterConfig.from_dict(reg_data)
            dev.registros.append(reg)

        return dev

