class ModbusTimeoutError(Exception):
    """Dispositivo não respondeu (porta OK)."""
    pass


class ModbusConnectionError(Exception):
    """Falha física de conexão (porta, socket, etc)."""
    pass


class ModbusRegisterError(Exception):
    """Erro específico de registro."""
    pass
