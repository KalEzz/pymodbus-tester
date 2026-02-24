from dataclasses import dataclass
from typing import Optional


@dataclass
class PollResult:
    reg: object
    value: Optional[float]
    error: Optional[str] = None
