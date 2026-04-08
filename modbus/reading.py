from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Reading:
    device_id: str
    device_name: str
    register_name: str
    address: int

    value: Optional[float]
    timestamp: Optional[datetime]
    error: Optional[str]