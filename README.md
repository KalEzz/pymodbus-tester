# PyModbus Tester

PyModbus Tester is a desktop application built with PySide and pymodbus for testing, monitoring, and managing Modbus devices (RTU and TCP).

> ⚠️ Project under development – current version: v0.1.0

---

## 🚀 Features

- Support for Modbus RTU and TCP
- Real-time register polling
- Holding and Input register visualization
- Device configuration interface
- Organized tree view for registers
- Modular architecture 

---

## 🏗️ Project Structure
```
pymodbus-tester/
│
├── icons/
├── images/
├── modbus/
├── models/
├── ui/
│
├── config/
│   └── config_manager.py
│
├── core/
│   ├── custom_theme.py
│   └── utils.py
│
├── main.py
│
├── README.md
├── requirements.txt
├── .gitignore
```

---

## 🧠 Architecture

The project is divided into:

- **UI Layer** → PySide interface components
- **Models Layer** → Device and configuration models
- **Modbus Layer** → Communication logic, polling and decoding
- **Core Utilities** → Shared utilities and theme system

---

## ⚙️ Requirements

- Python 3.10+
- PySide6
- pymodbus

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Application

```bash
python main.py
```
---

## 📌 Roadmap

- Improve async Modbus runtime
- Device auto-reconnect
- Logging system
- Export register data in CSV
- Executable for run application
- Installer build

---

## 👨‍💻 Author

Kauan Enzo (KalEzz)

---

## 📄 License

This project is currently private / experimental.

