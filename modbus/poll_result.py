from dataclasses import dataclass
from typing import Optional


@dataclass
class PollResult:
    def __init__(self, device, reg, value=None, error=None):
        self.device = device
        self.reg = reg
        self.value = value
        self.error = error