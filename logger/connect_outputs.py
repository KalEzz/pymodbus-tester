from datetime import datetime

from core.utils import get_user
from logger.csv_logger import CSVLogger


def connect_outputs(runtime, devices):
    csv_logger = CSVLogger(f"C:/Users/{get_user()}/Desktop/LeiturasPyModbusTester/{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv")

    def handler(reading):
        device = devices.get(reading.device_id)
        log_enabled = getattr(device, "log_enabled", "False")
        if device:
            if log_enabled == "True":
                csv_logger.handle_reading(reading)

    runtime.value_updated.connect(handler)