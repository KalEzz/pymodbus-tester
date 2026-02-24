import asyncio
from PySide6.QtCore import QObject, Signal
from modbus.errors import (
    ModbusTimeoutError,
    ModbusConnectionError,
)


class ModbusRuntime(QObject):
    value_updated = Signal(object, object)
    device_state_changed = Signal(object, str)
    error_occurred = Signal(object, str)

    def __init__(self, devices, poller, client_manager, interval=1.0):
        super().__init__()
        self.devices = devices
        self.poller = poller
        self.client_manager = client_manager
        self.interval = interval

        self._running = False
        self._task: asyncio.Task | None = None

        self.device_states = {d: "STOPPED" for d in devices}
        self.failure_count = {d: 0 for d in devices}
        self.max_failures_before_reconnect = 5

    # -------------------------
    # Estado por device
    # -------------------------

    def _set_state(self, device, state, error=None):
        if self.device_states.get(device) != state:
            self.device_states[device] = state
            self.device_state_changed.emit(device, state)
            print(f"Device {device.dev_id} - {device.nome}: {state}")

        if error:
            self.error_occurred.emit(device, error)

    # -------------------------
    # API pública
    # -------------------------

    def start(self):
        if self._running:
            return

        self._running = True
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run())

        print("Leitura Iniciada")

    async def stop(self):
        self._running = False

        if self._task:
            self._task.cancel()
            self._task = None

        await self.client_manager.close_all()
        print("Leitura Encerrada")


    def update_context(self, devices, interval, timeout):
        """
        Atualiza completamente o contexto de leitura.
        Deve ser chamado SEMPRE com o runtime parado.
        """

        if self._running:
            raise RuntimeError("Não pode atualizar contexto com runtime rodando")

        print("[RUNTIME] Atualizando contexto...")

        self.devices = devices
        self.interval = interval

        # Atualiza timeout do ClientManager
        self.client_manager.timeout = timeout

        # Força recriação de clients
        self.client_manager.clients.clear()
        self.client_manager.device_map.clear()

        # Reset estados e contadores
        self.device_states = {d: "STOPPED" for d in devices}
        self.failure_count = {d: 0 for d in devices}

        print("[RUNTIME] Contexto atualizado")

    # -------------------------
    # Loop principal
    # -------------------------

    async def _run(self):
        try:
            while self._running:
                print(f"[RUNTIME] Novo Ciclo de Leitura - {len(self.devices)} Devices no Ciclo")

                tasks = [
                    self._poll_device(device)
                    for device in self.devices.values()
                ]

                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(self.interval)

        except asyncio.CancelledError:
            pass

    # -------------------------
    # Poll individual
    # -------------------------

    async def _poll_device(self, device):
        if device.enabled == "True":
            print(f"[RUNTIME] entrando no poll do Device {device.dev_id} {device.nome}")

            try:
                print(f"[RUNTIME] - Device {device.dev_id} - Pedindo Client")
                client = await self.client_manager.get_client(device)

                if not client.connected:
                    raise ModbusConnectionError("Client não conectado")

                print(f"[RUNTIME] - Device {device.dev_id} - Client OK")

                results = await self.poller.poll_device(device, client)

                has_timeout = False
                has_connection_error = False

                for result in results:

                    if result.error:

                        if isinstance(result.error, ModbusTimeoutError):
                            has_timeout = True

                        elif isinstance(result.error, ModbusConnectionError):
                            has_connection_error = True

                        else:
                            print(f"[ERRO] - Device {device.dev_id} Registro: {result.error}")
                            self.error_occurred.emit(device, str(result.error))

                        continue

                    # sucesso
                    self.failure_count[device] = 0
                    result.reg.last_value = result.value
                    self.value_updated.emit(result.reg, result.value)

                # -------- Tratamento de estados --------

                if has_connection_error:
                    print(f"[ERRO][_POLL] - Device {device.dev_id}: Erro de conexão")
                    raise ModbusConnectionError("Erro de conexão detectado")

                if has_timeout:
                    self.failure_count[device] += 1
                    print(f"[RUNTIME] Device {device.dev_id} Timeout ({self.failure_count[device]})")
                    self._set_state(device, "OFFLINE")

                    if self.failure_count[device] >= self.max_failures_before_reconnect:
                        print(f"[RUNTIME] Device {device.dev_id} excedeu limite de falhas. Tentando reconnect.")
                        await self._try_reconnect(device)

                else:
                    self._set_state(device, "RUNNING")

            except ModbusConnectionError as e:
                print(f"[ERRO][_POLL] - Device {device.dev_id}: {e}")
                await self._try_reconnect(device)

            except Exception as e:
                print(f"[ERRO][_POLL][UNEXPECTED] - Device {device.dev_id}: {e}")
                self._set_state(device, "ERROR", str(e))
        else:
            print(f"[RUNTIME] Device {device.dev_id} {device.nome} - Desabilitado")
    # -------------------------
    # Reconnect
    # -------------------------

    async def _try_reconnect(self, device):
        self._set_state(device, "RECONNECTING")

        try:
            await self.client_manager.reconnect(device)
            self.failure_count[device] = 0
            print(f"[RUNTIME] Device {device.dev_id} Reconnect OK")
            self._set_state(device, "RUNNING")

        except Exception as e:
            print(f"[ERRO][try_reconnect] - Device {device.dev_id}: {e}")
            self._set_state(device, "ERROR", str(e))
