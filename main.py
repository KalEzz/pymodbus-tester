import sys
import asyncio

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from logger.connect_outputs import connect_outputs

from ui.main_window import App

from modbus.runtime import ModbusRuntime
from modbus.poller import ModbusPoller
from modbus.decoder import Decoder
from modbus.clients import ClientManager

from config.config_manager import load_program_settings, load_devices


def main():
    # =============================
    # Qt + asyncio
    # =============================
    app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # =============================
    # Carrega configurações
    # =============================
    settings = load_program_settings()
    devices = load_devices()

    # =============================
    # Backend Modbus
    # =============================
    decoder = Decoder()

    client_manager = ClientManager(
        timeout=settings.timeout
    )

    poller = ModbusPoller(
        decoder=decoder
    )

    runtime = ModbusRuntime(
        devices=devices,
        poller=poller,
        client_manager=client_manager,
        interval=settings.intervalo_de_leitura
    )

    # =============================
    # Logger
    # =============================
    #connect_outputs(runtime, devices)

    # =============================
    # UI
    # =============================
    window = App(runtime)
    window.show()

    # =============================
    # Loop principal
    # =============================
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
