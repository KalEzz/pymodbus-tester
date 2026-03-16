import asyncio
import time
from datetime import datetime

from PySide6.QtCore import QObject, Signal


class ModbusRuntime(QObject):
    value_updated = Signal(object, int)  # device, endereco do registro
    device_state_changed = Signal(object, str)
    error_occurred = Signal(object, str)

    STOPPED = "STOPPED"
    CONNECTING = "CONNECTING"
    RUNNING = "RUNNING"
    OFFLINE = "OFFLINE"
    DISABLED = "DISABLED"

    def __init__(self, devices, poller, client_manager, interval=1.0):
        super().__init__()

        self.devices = devices
        self.poller = poller
        self.client_manager = client_manager
        self.interval = interval

        self._running = False
        self._task = None

        #  Controle de falhas
        self.max_failures = 5
        self.reconnect_delay = 3  # segundos

        self.device_states = {
            d.dev_id: self.STOPPED for d in devices.values()
        }

        self.failure_count = {
            d.dev_id: 0 for d in devices.values()
        }

        self.last_reconnect_attempt = {
            d.dev_id: 0 for d in devices.values()
        }

    # --------------------------------------------------
    # ESTADO
    # --------------------------------------------------

    def _set_state(self, device, state, error=None):
        dev_id = device.dev_id
        current = self.device_states.get(dev_id)

        if current != state:
            self.device_states[dev_id] = state
            self.device_state_changed.emit(device, state)
            print(f"Device {dev_id} - {device.nome}: {state}")

        if error:
            self.error_occurred.emit(device, error)

    # --------------------------------------------------
    # API
    # --------------------------------------------------

    def start(self):
        if self._running:
            return

        self._running = True

        for device in self.devices.values():
            self._set_state(device, self.CONNECTING)

        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run())

        print("Leitura Iniciada")

    async def stop(self):
        self._running = False

        if self._task:
            self._task.cancel()
            self._task = None

        await self.client_manager.close_all()

        for device in self.devices.values():
            self._set_state(device, self.STOPPED)

        print("Leitura Encerrada")

    # --------------------------------------------------
    # LOOP
    # --------------------------------------------------

    async def _run(self):
        try:
            while self._running:

                print(f"[RUNTIME] Novo Ciclo - {len(self.devices)} Devices")

                tasks = []

                for device in self.devices.values():

                    if device.enabled == "True":
                        tasks.append(self._poll_device(device))

                    else:
                        if self.device_states[device.dev_id] != self.DISABLED:
                            self._set_state(device, self.DISABLED)

                await asyncio.gather(*tasks)
                await asyncio.sleep(self.interval)

        except asyncio.CancelledError:
            pass

    # --------------------------------------------------
    # POLL
    # --------------------------------------------------

    async def _poll_device(self, device):

        dev_id = device.dev_id
        state = self.device_states[dev_id]

        print(f"\n[RUNTIME] --- DEVICE {dev_id} ---")
        print(f"[RUNTIME] Estado atual: {state}")
        print(f"[RUNTIME] Falhas atuais: {self.failure_count[dev_id]}")

        # --------------------------------------------------
        # OFFLINE → aguarda cooldown
        # --------------------------------------------------
        if state == self.OFFLINE:

            now = time.time()
            offline_time = now - self.last_reconnect_attempt[dev_id]

            print(f"[RUNTIME] Está OFFLINE há {offline_time:.2f}s")
            print(f"[RUNTIME] reconnect_delay = {self.reconnect_delay}s")

            if offline_time < self.reconnect_delay:
                print("[RUNTIME] Ainda em cooldown, não vai tentar conectar.")
                return

            print("[RUNTIME] Cooldown terminou → vai tentar conectar novamente")

            self.last_reconnect_attempt[dev_id] = now
            self.failure_count[dev_id] = 0

        try:

            # Sempre que for tentar comunicação
            if self.device_states[dev_id] != self.RUNNING:
                print("[RUNTIME] Mudando estado para CONNECTING")
                self._set_state(device, self.CONNECTING)

            print("[RUNTIME] Chamando get_client()")
            client = await self.client_manager.get_client(device)

            print("[RUNTIME] Chamando poll_device()")
            results = await self.poller.poll_device(device, client)

            if not results:
                raise ConnectionError("Nenhuma resposta do dispositivo")

            success = False

            for result in results:

                reg = result.reg

                if result.error:
                    print(f"[RUNTIME] Registrador erro: {result.error}")
                    reg.last_error = result.error
                    reg.last_value = None

                elif result.value is None:
                    print("[RUNTIME] Registrador sem resposta")
                    reg.last_error = "Sem resposta"
                    reg.last_value = None

                else:
                    print(f"[RUNTIME] Registrador OK → {result.value}")
                    reg.last_error = None
                    reg.last_value = result.value
                    reg.last_timestamp = datetime.now()
                    success = True

                self.value_updated.emit(device, int(reg.endereco))

            if not success:
                raise ConnectionError("Nenhum registrador respondeu")

            # -------------------------
            # SUCESSO REAL
            # -------------------------
            print("[RUNTIME] Comunicação OK → RUNNING")

            self.failure_count[dev_id] = 0
            self._set_state(device, self.RUNNING)

        except Exception as e:

            self.failure_count[dev_id] += 1

            print(f"[RUNTIME] ERRO CAPTURADO: {e}")
            print(f"[RUNTIME] Falhas agora: {self.failure_count[dev_id]}")
            print(f"[RUNTIME] max_failures: {self.max_failures}")

            if self.failure_count[dev_id] < self.max_failures:
                print("[RUNTIME] Ainda não atingiu limite → permanece CONNECTING")
                self._set_state(device, self.CONNECTING, str(e))
                return

            # Estourou limite
            print("[RUNTIME] LIMITE ATINGIDO → indo para OFFLINE")

            self._set_state(device, self.OFFLINE, str(e))
            self.last_reconnect_attempt[dev_id] = time.time()

            print("[RUNTIME] Chamando disconnect()")
            await self.client_manager.disconnect(device)

    # --------------------------------------------------
    # UPDATE CONTEXT
    # --------------------------------------------------

    def update_context(self, devices, interval, timeout):
        """
        Atualiza completamente o contexto de leitura.
        O runtime DEVE estar parado antes de chamar.
        """

        if self._running:
            raise RuntimeError(
                "Não pode atualizar contexto com runtime rodando"
            )

        print("[RUNTIME] Atualizando contexto...")

        # Atualiza referências principais
        self.devices = devices
        self.interval = interval

        # Atualiza timeout do ClientManager
        self.client_manager.timeout = timeout

        #  Fecha qualquer client antigo por segurança
        # (caso alguém tenha chamado fora da ordem)
        try:
            asyncio.create_task(self.client_manager.close_all())
        except RuntimeError:
            # caso não exista loop ativo
            pass

        #  Limpa caches internos do ClientManager
        self.client_manager.clients.clear()
        self.client_manager.device_map.clear()

        #  Reseta estados
        self.device_states = {
            d.dev_id: self.STOPPED for d in devices.values()
        }

        #  Reseta contadores de falha
        self.failure_count = {
            d.dev_id: 0 for d in devices.values()
        }

        #  Reseta controle de reconnect
        self.last_reconnect_attempt = {
            d.dev_id: 0 for d in devices.values()
        }

        print("[RUNTIME] Contexto atualizado")