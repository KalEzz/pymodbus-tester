import struct


class Decoder:
    """
    Responsável por converter dados Modbus brutos (bytes)
    em valores já tratados conforme a configuração do registro.
    """

    # =========================
    # API pública
    # =========================

    def decode(self, reg, raw: bytes):
        """
        Decodifica um valor único (single ou extraído de bloco).
        """
        return self._apply_pipeline(reg, raw)

    # =========================
    # Pipeline interno
    # =========================

    def _apply_pipeline(self, reg, raw: bytes):
        """
        Pipeline completo:
        1) valida
        2) reorder (word / byte)
        3) decode datatype
        4) aplica escala
        """
        self._validate_raw(reg, raw)

        data = self._reorder(raw, reg)
        value = self._decode_datatype(reg, data)
        value = self._apply_scale(reg, value)

        return value

    # =========================
    # Etapas do pipeline
    # =========================

    def _validate_raw(self, reg, raw: bytes):
        if len(raw) != reg.size:
            raise ValueError(
                f"Tamanho inválido do raw ({len(raw)}) "
                f"esperado {reg.size} para {reg.datatype}"
            )

    def _reorder(self, raw: bytes, reg):
        data = list(raw)

        # WORD ORDER
        if reg.word_order == "LITTLE" and len(data) > 2:
            words = [data[i:i + 2] for i in range(0, len(data), 2)]
            data = sum(words[::-1], [])

        # BYTE ORDER
        if reg.byte_order == "LITTLE":
            words = [data[i:i + 2] for i in range(0, len(data), 2)]
            data = sum([word[::-1] for word in words], [])

        return bytes(data)

    def _decode_datatype(self, reg, data: bytes):
        fmt_map = {
            "UINT16": ">H",
            "INT16": ">h",
            "UINT32": ">I",
            "INT32": ">i",
            "FLOAT32": ">f",
        }

        fmt = fmt_map.get(reg.datatype)
        if not fmt:
            raise ValueError(f"Datatype inválido: {reg.datatype}")

        return struct.unpack(fmt, data)[0]

    def _apply_scale(self, reg, value):
        if reg.divisor:
            value /= float(reg.divisor)

        if reg.offset:
            value += float(reg.offset)

        return value
