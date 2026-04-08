from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusDeviceContext, ModbusServerContext

import threading
import time
import math
import random

# ==============================
# Criando registradores
# ==============================

store = ModbusDeviceContext(
    hr=ModbusSequentialDataBlock(0, [0]*100)
)

context = ModbusServerContext(
    devices={1: store},  # unit_id = 1
    single=False
)

# ==============================
# Atualização dinâmica
# ==============================

def update_registers():
    t = 0
    while True:
        device = context[1]

        device.setValues(3, 0, [t])

        sine_value = int(50 + 50 * math.sin(t / 5))
        device.setValues(3, 1, [sine_value])

        rand_value = random.randint(0, 1000)
        device.setValues(3, 2, [rand_value])

        temp = int(20 + 10 * math.sin(t / 10))
        device.setValues(3, 3, [temp])

        status = t % 2
        device.setValues(3, 4, [status])

        block = [random.randint(0, 500) for _ in range(5)]
        device.setValues(3, 5, block)

        t += 1
        time.sleep(1)

threading.Thread(target=update_registers, daemon=True).start()

# ==============================
# Inicializando servidor
# ==============================

IP = "127.0.0.1"
PORT = 5020

print(f"🚀 Modbus TCP Simulator rodando em {IP}:{PORT}")
print("👉 Unit ID: 1")

StartTcpServer(context, address=(IP, PORT))