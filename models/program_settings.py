class ProgramSettings:
    def __init__(
        self,
        max_read_per_file=20000,
        intervalo_de_leitura=1,
        timeout=1000,
        theme_color="dark"
    ):
        self.max_read_per_file = int(max_read_per_file)
        self.intervalo_de_leitura = int(intervalo_de_leitura)
        self.timeout = int(timeout)
        self.theme_color = theme_color


    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            max_read_per_file=data.get("max_read_per_file", 20000),
            intervalo_de_leitura=data.get("intervalo_de_leitura", 1),
            timeout=data.get("timeout", 1000),
            theme_color=data.get("theme_color", "dark")
        )

    def to_dict(self):
        return {
            "max_read_per_file": self.max_read_per_file,
            "intervalo_de_leitura": self.intervalo_de_leitura,
            "timeout": self.timeout,
            "theme_color": self.theme_color
        }
