import ctypes
from ctypes import wintypes

def custom_theme(
    bg_color="#2b2b2b",               # Cor de fundo principal
    bg_color2="#1e1e1e",              # Cor de fundo secundaria
    fg_color="#d1d1d1",               # Cor do texto principal
    accent_color="#3c78d8",           # Cor de destaque (botões, links)
    input_bg="#3c3f41",               # Fundo de inputs
    input_border="#555555",           # Cor da borda dos inputs
    btn_bg="transparent",
    hover_color="#3a3a3a",            # Cor de hover nos botões
    pressed_color="#444444",          # Cor de botão pressionado
    font_family="'Segoe UI', sans-serif",  # Fonte
    font_size="14px",                 # Tamanho da fonte
    border_radius="6px",              # Borda arredondada
    spacing="6px",                    # Espaçamento interno (padding)
    scrollbar_color="#555555"         # Cor da barra de rolagem
):
    return f"""
    QWidget {{
        background-color: {bg_color};
        color: {fg_color};
        font-family: {font_family};
        font-size: {font_size};
    }}
    QWidget#DeviceGrid{{
        background-color: {bg_color2};
        color: {fg_color};
        font-family: {font_family};
        font-size: {font_size};
    }}
    QWidget#TransparentWidget{{
        background-color: transparent;
        color: {fg_color};
        font-family: {font_family};
        font-size: {font_size};
    }}

    QPushButton {{
        background-color: {btn_bg};
        color: {fg_color};
        border-radius: {border_radius};
        padding: {spacing} {spacing};
    }}
    QPushButton:hover {{
        background-color: {hover_color};
    }}
    QPushButton:pressed {{
        background-color: {pressed_color};
    }}
    QPushButton#CloseButton{{
        background-color: transparent; 
        color: white; 
        border: none; 
        font-size: 14pt;
        margin: 0; 
        border-radius: 0px; 
        padding: 0; 
        font-size: 14pt; 
        font-weight: normal;
    }}
    QPushButton#CloseButton:hover {{
        background-color: #e74c3c;
    }}
    QPushButton#CloseButton:pressed {{
        background-color: #c0392b;
    }}
    QPushButton#RemoveDeviceButton{{
        background: #a33; 
        color: white; 
        border-radius: 4px;
    }}
    QPushButton#RemoveDeviceButton:hover {{
        background-color: #c44;
    }}  
       
     
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {input_bg};
        color: {fg_color};
        border: 1px solid {input_border};
        border-radius: {border_radius};
        padding: 4px;
    }}

    QTextEdit#ConsoleText {{
        color: {fg_color};
        background-color: #000000;
    }}

    QLabel {{
        color: {fg_color};
        background-color: transparent;
    }}
    QLabel#TransparentLabel {{
        color: {fg_color};
        background-color: transparent;
    }}


    QScrollBar:vertical {{
        background: {bg_color};
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {scrollbar_color};
        border-radius: 4px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        background: none;
        height: 0;
    }}



    QFrame {{
        background-color: {bg_color};
        border: none;
    }}
    QFrame#DeviceFrame{{
        background-color: {bg_color2};
        border: none;
    }}
    QFrame#DeviceWidgetFrame{{
        background-color: {bg_color};
        border: 1px solid #444;
        border-radius: 6px;
    }}
    QFrame#BgWindowFrame{{
        background-color: {bg_color2};
        border: none;
        
    }}
    QFrame#ConsoleFrame{{
        background-color: #000000;
        border: none;
        
    }}
    
    QTabBar::tab {{
        background: {input_bg};
        color: {fg_color};
        padding: 8px;
        border-top-left-radius: {border_radius};
        border-top-right-radius: {border_radius};
    }}
    QTabBar::tab:selected {{
        background: {accent_color};
    }}

    QToolTip {{
        background-color: {input_bg};
        color: {fg_color};
        border: 1px solid {input_border};
        padding: 4px;
    }}
    
        /* =========================
       QTreeView / QHeaderView
       ========================= */

    QTreeView {{
        background-color: {bg_color2};
        color: {fg_color};
        border: 1px solid {input_border};
        border-radius: {border_radius};
        show-decoration-selected: 1;
        alternate-background-color: {bg_color};
    }}

    QTreeView::item {{
        padding: 6px;
        border: none;
    }}

    QTreeView::item:hover {{
        background-color: {hover_color};
    }}

    QTreeView::item:selected {{
        background-color: {accent_color};
        color: white;
    }}

    QTreeView::item:selected:!active {{
        background-color: {pressed_color};
        color: white;
    }}

    /* Header */
    QHeaderView::section {{
        background-color: {input_bg};
        color: {fg_color};
        padding: 6px;
        border: 1px solid {input_border};
        font-weight: bold;
    }}

    QHeaderView::section:hover {{
        background-color: {hover_color};
    }}

    QHeaderView::section:pressed {{
        background-color: {pressed_color};
    }}

    /* Remove linha de foco azul padrão */
    QTreeView::item:selected:active {{
        outline: none;
    }}
    
    """


def set_dark_titlebar(window):
    hwnd = int(window.winId())  # pega o handle da janela

    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19

    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute

    # Tenta atributo 20 (Windows 11 e 10 recentes)
    value = ctypes.c_int(1)
    set_window_attribute(
        wintypes.HWND(hwnd),
        DWMWA_USE_IMMERSIVE_DARK_MODE,
        ctypes.byref(value),
        ctypes.sizeof(value)
    )

    # Tenta atributo 19 (Windows 10 mais antigo)
    set_window_attribute(
        wintypes.HWND(hwnd),
        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
        ctypes.byref(value),
        ctypes.sizeof(value)
    )