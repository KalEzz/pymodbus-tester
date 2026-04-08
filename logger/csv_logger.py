import csv
from pathlib import Path
from threading import Lock


class CSVLogger:
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self._lock = Lock()

        # garante que header seja escrito só uma vez
        self._initialized = False

    # --------------------------------------------------
    # INIT FILE
    # --------------------------------------------------

    def _initialize_file(self):
        if self.filepath.exists():
            self._initialized = True
            return

        with open(self.filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow([
                "timestamp",
                "device_id",
                "device_name",
                "register_name",
                "address",
                "value",
                "error"
            ])

        self._initialized = True

    # --------------------------------------------------
    # HANDLER (PLUG NO SIGNAL)
    # --------------------------------------------------

    def handle_reading(self, reading):
        """
        reading = dataclass PullResult
        """

        # proteção pra multithread (Qt + asyncio)
        with self._lock:

            if not self._initialized:
                self._initialize_file()

            with open(self.filepath, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                writer.writerow([
                    reading.timestamp,
                    reading.device_id,
                    reading.device_name,
                    reading.register_name,
                    reading.address,
                    reading.value,
                    reading.error
                ])