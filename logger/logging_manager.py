from datetime import datetime
from pathlib import Path

from core.utils import get_user
from logger.csv_logger import CSVLogger


class LoggingManager:
    def __init__(self, runtime, devices):
        self.runtime = runtime
        self.devices = devices

        self.logger = None
        self._handler = None

    # ----------------------------------------
    # START LOGGING
    # ----------------------------------------

    def start(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        path = Path(
            f"C:/Users/{get_user()}/Desktop/LeiturasPyModbusTester"
        )
        path.mkdir(parents=True, exist_ok=True)

        file = path / f"{timestamp}.csv"

        self.logger = CSVLogger(file)

        def handler(reading):
            device = self.devices.get(reading.device_id)

            if not device:
                return

            log_enabled = getattr(device, "log_enabled", "False")

            if str(log_enabled) == "True":
                self.logger.handle_reading(reading)

        self._handler = handler

        self.runtime.value_updated.connect(self._handler)

    # ----------------------------------------
    # STOP LOGGING
    # ----------------------------------------

    def stop(self):
        if self._handler:
            try:
                self.runtime.value_updated.disconnect(self._handler)
            except Exception:
                pass

        self.logger = None
        self._handler = None