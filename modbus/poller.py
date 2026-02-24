import asyncio

from modbus.poll_result import PollResult
from core.utils import parse_address_ranges
from modbus.errors import (
    ModbusTimeoutError,
    ModbusRegisterError
)


class ModbusPoller:
    def __init__(self, decoder):
        self.decoder = decoder

    async def poll_device(self, device, client):
        results = []
        print(f"[POLLER] Device {device.dev_id} {device.nome}")

        # =========================
        # Verificação de Conexão
        # =========================
        if not client.connected:
            msg = f"[ERRO] Device {device.nome} ({device.endereco}) não conectado."
            print(msg)

            for reg in device.registros:
                if reg.enabled:
                    results.append(
                        PollResult(reg=reg, value=None, error="Device não conectado")
                    )
            return results

        for reg in device.registros:
            if reg.enabled == "False":
                continue

            try:
                # =========================
                # Parse de endereço
                # =========================
                start, qty = parse_address_ranges(reg.endereco)

                # =========================
                # Leitura Modbus
                # =========================
                try:
                    response = await asyncio.wait_for(
                        self._read_register(
                            client,
                            reg,
                            start,
                            qty,
                            int(device.endereco)
                        ),
                        timeout=device.timeout if hasattr(device, "timeout") else 5
                    )
                except asyncio.TimeoutError:
                    raise ModbusTimeoutError("[ERRO] Timeout da aplicação Modbus")

                if not response:
                    raise ModbusTimeoutError(f"[ERRO] - Sem resposta do Device {device.dev_id} {device.nome}")

                if response.isError():
                    print(f"[ERRO] - Leitura[Raw] - Registro {reg.endereco}: {response}")
                    raise ModbusTimeoutError(str(response))

                # =========================
                # Decode
                # =========================
                if reg.tipo.lower() in ["coil", "discrete"]:
                    raw = response.bits
                    raw_bytes = bytes(raw)
                else:
                    raw = response.registers
                    raw_bytes = b''.join(
                        r.to_bytes(2, byteorder="big")
                        for r in raw
                    )

                print(f"Leitura[Raw] - Registro{reg.endereco}: {raw}")

                if qty == 1:
                    value = self.decoder.decode(reg, raw_bytes)
                    results.append(PollResult(reg=reg, value=value))
                    print(f"Leitura[Decode] - Registro {reg.endereco}: {value}")
                else:
                    values = self.decoder.decode_block(reg, raw_bytes)
                    for value in values:
                        results.append(PollResult(reg=reg, value=value))
                        print(f"Leitura[Decode] >1 - Registro {reg.endereco}: {value}")

            except ModbusTimeoutError as e:
                results.append(
                    PollResult(reg=reg, value=None, error=str(e))
                )
                print(f"[ERRO] - Leitura[Decode] - Registro {reg.endereco}: {e}")

            except Exception as e:
                # Erro de registro apenas
                results.append(
                    PollResult(reg=reg, value=None, error=str(e))
                )
                print(f"[ERRO] - Leitura[Decode] - Registro {reg.endereco}: {e}")

        return results

    # =========================
    # Escolha de Registro
    # =========================
    async def _read_register(self, client, reg, start, qty, slave):
        tipo = reg.funcao.lower()

        if tipo == "holding":
            return await client.read_holding_registers(address=start, count=qty, slave=slave)

        elif tipo == "input":
            return await client.read_input_registers(address=start, count=qty, slave=slave)

        elif tipo == "coil":
            return await client.read_coils(address=start, count=qty, slave=slave)

        elif tipo == "discrete":
            return await client.read_discrete_inputs(address=start, count=qty, slave=slave)

        else:
            raise ModbusRegisterError(f"[ERRO]Função inválida: {reg.funcao}")
