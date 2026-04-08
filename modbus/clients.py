class ClientManager:
    def __init__(self, timeout):
        self.timeout = timeout
        self.clients = {}
        self.device_map = {}

    async def get_client(self, device):
        key = self._make_key(device)

        client = self.clients.get(key)

        if client is None:
            print("[CLIENT MANAGER] Criando novo client")
            client = await device.create_client(self.timeout)
            self.clients[key] = client

        print("[CLIENT MANAGER] Conectando client...")

        connected = await client.connect()

        if not connected:
            raise ConnectionError("Falha ao conectar")

        self.device_map[device.dev_id] = key
        return client

    async def disconnect(self, device):
        key = self.device_map.get(device)

        if not key:
            return

        client = self.clients.get(key)

        if client:
            try:
                print("[CLIENT MANAGER] Fechando client")
                client.close()
            except Exception as e:
                print("[CLIENT MANAGER] Erro ao fechar:", e)

        # Remove completamente
        self.clients.pop(key, None)
        self.device_map.pop(device, None)

    async def close_all(self):
        for device in list(self.device_map.keys()):
            await self.disconnect(device)

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