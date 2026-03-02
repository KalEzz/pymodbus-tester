import asyncio
from modbus.poll_result import PollResult
from modbus.errors import ModbusTimeoutError, ModbusRegisterError


class ModbusPoller:

    MAX_REG_BLOCK = 120  # limite seguro (evita problemas em alguns devices)

    def __init__(self, decoder):
        self.decoder = decoder

    # ==========================================================
    # POLL PRINCIPAL
    # ==========================================================
    async def poll_device(self, device, client):
        results = []

        print(f"[POLLER] Device {device.dev_id} {device.nome}")

        if not client.connected:
            return self._build_not_connected_results(device)

        enabled_regs = [
            r for r in device.registros
            if r.enabled == "True"
        ]

        groups = self._group_registers(enabled_regs)

        for group in groups:
            group_results = await self._process_group(device, client, group)
            results.extend(group_results)

        return results

    # ==========================================================
    # PROCESSAMENTO DE GRUPO
    # ==========================================================
    async def _process_group(self, device, client, group):

        try:
            return await self._read_group_block(device, client, group)

        except Exception as e:
            print(f"[FALLBACK] Grupo falhou → tentando individual: {e}")
            return await self._fallback_individual(device, client, group)

    # ==========================================================
    # LEITURA EM BLOCO
    # ==========================================================
    async def _read_group_block(self, device, client, group):

        start = int(group[0].endereco)

        last = group[-1]
        last_end = int(last.endereco) + (last.size // 2) - 1

        qty = last_end - start + 1

        if qty > self.MAX_REG_BLOCK:
            raise Exception("Bloco excede limite máximo permitido")

        response = await asyncio.wait_for(
            self._read_register(
                client,
                group[0],
                start,
                qty,
                int(device.endereco)
            ),
            timeout=getattr(device, "timeout", 5)
        )

        if not response or response.isError():
            raise ModbusTimeoutError(str(response))

        # Monta bloco bruto
        if group[0].funcao.lower() in ["coil", "discrete"]:
            raw_block = bytes(response.bits)
        else:
            raw_block = b''.join(
                r.to_bytes(2, byteorder="big")
                for r in response.registers
            )

        results = []

        for reg in group:
            try:
                reg_start = int(reg.endereco)
                offset = (reg_start - start) * 2
                length = reg.size

                raw_slice = raw_block[offset:offset + length]

                value = self.decoder.decode(reg, raw_slice)

                results.append(
                    PollResult(device=device, reg=reg, value=value)
                )

                print(f"[OK] Device {device.dev_id} Reg {reg.endereco}: {value}")

            except Exception as decode_error:
                results.append(
                    PollResult(device=device, reg=reg, value=None, error=str(decode_error))
                )
                print(f"[DECODE ERROR] Device {device.dev_id} Reg {reg.endereco}: {decode_error}")

        return results

    # ==========================================================
    # FALLBACK INDIVIDUAL
    # ==========================================================
    async def _fallback_individual(self, device, client, group):

        results = []

        for reg in group:
            try:
                start = int(reg.endereco)
                qty = reg.size // 2

                response = await asyncio.wait_for(
                    self._read_register(
                        client,
                        reg,
                        start,
                        qty,
                        int(device.endereco)
                    ),
                    timeout=getattr(device, "timeout", 5)
                )

                if not response or response.isError():
                    raise ModbusTimeoutError(f"Device {device.dev_id} Reg {reg.endereco} - {str(response)}")

                if reg.funcao.lower() in ["coil", "discrete"]:
                    raw_bytes = bytes(response.bits)
                else:
                    raw_bytes = b''.join(
                        r.to_bytes(2, byteorder="big")
                        for r in response.registers
                    )

                value = self.decoder.decode(reg, raw_bytes)

                results.append(
                    PollResult(device=device, reg=reg, value=value)
                )

                print(f"[FALLBACK OK] Device - {device.dev_id} Reg {reg.endereco}: {value}")

            except Exception as e:
                results.append(
                    PollResult(device=device, reg=reg, value=None, error=str(e))
                )
                print(f"[FALLBACK ERROR] Device - {device.dev_id} Reg {reg.endereco}: {e}")

        return results

    # ==========================================================
    # AGRUPAMENTO INTELIGENTE
    # ==========================================================
    def _group_registers(self, registers):

        groups = []

        sorted_regs = sorted(registers, key=lambda r: int(r.endereco))

        current_group = []
        last_end = None
        last_func = None

        for reg in sorted_regs:
            start = int(reg.endereco)
            length = reg.size // 2
            end = start + length - 1

            if (
                last_end is None or
                (start == last_end + 1 and reg.funcao == last_func)
            ):
                current_group.append(reg)
            else:
                groups.append(current_group)
                current_group = [reg]

            last_end = end
            last_func = reg.funcao

        if current_group:
            groups.append(current_group)

        return groups

    # ==========================================================
    # LEITURA POR FUNÇÃO
    # ==========================================================
    async def _read_register(self, client, reg, start, qty, slave):

        tipo = reg.funcao.lower()

        if tipo == "holding":
            return await client.read_holding_registers(start, qty, slave)

        elif tipo == "input":
            return await client.read_input_registers(start, qty, slave)

        elif tipo == "coil":
            return await client.read_coils(start, qty, slave)

        elif tipo == "discrete":
            return await client.read_discrete_inputs(start, qty, slave)

        else:
            raise ModbusRegisterError(f"Função inválida: {reg.funcao}")

    # ==========================================================
    # DEVICE NÃO CONECTADO
    # ==========================================================
    def _build_not_connected_results(self, device):

        results = []

        for reg in device.registros:
            if reg.enabled == "True":
                results.append(
                    PollResult(
                        device=device,
                        reg=reg,
                        value=None,
                        error="Device não conectado"
                    )
                )
                print(f"[ERROR] Device - {device.dev_id} Reg {reg.endereco}: Device não Conectado")
        return results