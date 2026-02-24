import os
import json
from models.device import Device
from models.program_settings import ProgramSettings


base_dir = os.getenv("APPDATA")
config_dir = os.path.join(base_dir, "MicTeste Modbus", "config")

os.makedirs(config_dir, exist_ok=True)

program_config_file = os.path.join(config_dir, 'program_settings.json')
device_config_file = os.path.join(config_dir, 'device_settings.json')


def load_program_settings():
    if os.path.exists(program_config_file):
        try:
            with open(program_config_file, 'r') as f:
                data = json.load(f)
                return ProgramSettings.from_dict(data)
        except (json.JSONDecodeError, ValueError):
            # Arquivo corrompido ou vazio
            return ProgramSettings()

    return ProgramSettings()


def load_devices():
    devices = {}

    if os.path.exists(device_config_file):
        with open(device_config_file, 'r') as file:
            data = json.load(file)

        for dev_id, dev_data in data.items():
            devices[dev_id] = Device.from_dict(dev_id, dev_data)

    else:
        # Cria 3 devices padrão se não existir arquivo
        for i in range(1, 4):
            devices[str(i)] = Device(str(i))

    return devices


def save_devices(devices):
    data = {}

    for dev_id, device in devices.items():
        data[dev_id] = device.to_dict()

    with open(device_config_file, 'w') as file:
        json.dump(data, file, indent=4)


def save_program_settings(program_settings: dict):
    with open(program_config_file, 'w') as file:
        json.dump(program_settings, file, indent=4)

