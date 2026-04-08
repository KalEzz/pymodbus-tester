class RegisterConfig:
    def __init__(self):
        # Identificação
        self.id: str = ""
        self.nome: str = ""

        # Modbus
        self.funcao: str = "holding"
        self.endereco: str = ""
        self.quantidade: int = 1
        self.modo_leitura: str = "AUTO"

        # Conversão
        self.datatype: str = "UINT16"
        self.divisor: float = 1.0
        self.offset: float = 0.0
        self.formula: str | None = None

        # Metadados
        self.unidade_medida: str = ""

        # Endianness
        self.byte_order: str = "BIG"
        self.word_order: str = "BIG"
        self.signed: str = "False"

        # Validação
        self.min_value: float | None = None
        self.max_value: float | None = None

        # Controle
        self.enabled: str = "True"

        # Historico de Leituras
        self.last_value = None
        self.last_error = None
        self.last_timestamp = None

    @property
    def size(self) -> int:
        datatype_sizes = {
            "UINT16": 2,
            "INT16": 2,
            "UINT32": 4,
            "INT32": 4,
            "FLOAT32": 4,
        }

        if self.datatype not in datatype_sizes:
            raise ValueError(f"Datatype inválido: {self.datatype}")

        return datatype_sizes[self.datatype]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "funcao": self.funcao,
            "endereco": self.endereco,
            "quantidade": self.quantidade,
            "modo_leitura": self.modo_leitura,
            "datatype": self.datatype,
            "divisor": self.divisor,
            "offset": self.offset,
            "formula": self.formula,
            "unidade_medida": self.unidade_medida,
            "byte_order": self.byte_order,
            "word_order": self.word_order,
            "signed": self.signed,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RegisterConfig":
        reg = cls()

        reg.id = data.get("id", "")
        reg.nome = data.get("nome", "")

        reg.funcao = data.get("funcao", "holding")
        reg.endereco = data.get("endereco")
        reg.quantidade = data.get("quantidade", 1)
        reg.modo_leitura = data.get("modo_leitura", "AUTO")

        reg.datatype = data.get("datatype", "UINT16")
        reg.divisor = data.get("divisor", 1.0)
        reg.offset = data.get("offset", 0.0)
        reg.formula = data.get("formula")

        reg.unidade_medida = data.get("unidade_medida", "")

        reg.byte_order = data.get("byte_order", "BIG")
        reg.word_order = data.get("word_order", "BIG")
        reg.signed = data.get("signed", "False")

        reg.min_value = data.get("min_value")
        reg.max_value = data.get("max_value")

        reg.enabled = data.get("enabled", "True")

        return reg