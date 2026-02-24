class ClientManager:
    def __init__(self, timeout):
        self.timeout = timeout
        self.clients = {}
        self.device_map = {}

    async def get_client(self, device):
        key = self._make_key(device)

        if key not in self.clients:
            client = await device.create_client(self.timeout)

            if not client.connected:
                await client.connect()

            self.clients[key] = client

        self.device_map[device] = key
        return self.clients[key]

    async def reconnect(self, device):
        key = self.device_map.get(device)

        if not key:
            raise ConnectionError("Device não registrado")

        client = self.clients[key]

        try:
            client.close()
        except:
            pass

        await client.connect()

        if not client.connected:
            raise ConnectionError("Reconnect falhou")

    async def close_all(self):
        for client in self.clients.values():
            try:
                client.close()
            except:
                pass

        self.clients.clear()
        self.device_map.clear()

    def _make_key(self, device):
        if device.tipo_conexao == "tcp":
            return ("tcp", device.ip, device.porta)

        return (
            "rtu",
            device.porta_com,
            device.baudrate,
            device.paridade,
            device.bits_parada,
            device.tamanho_byte
        )
