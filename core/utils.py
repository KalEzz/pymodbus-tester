import getpass, os
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon, Qt
from PySide6.QtCore import QSize

def get_user():
    return getpass.getuser()

def create_directory(path):
    directory = 'C:/Users/' + get_user() + path

    if not os.path.exists(directory):
        os.makedirs(directory)

def open_directory(path):
    directory = 'C:/Users/' + get_user() + path

    if not os.path.exists(directory):
        os.makedirs(directory)

    os.startfile(directory)

def parse_address_ranges(text: str) -> tuple[int, int]:
    """
    Ex:
    "7"     -> (7, 1)
    "7-8"   -> (7, 2)
    "7-10"  -> (7, 4)
    """

    text = text.strip()

    if "-" in text:
        start, end = text.split("-")
        start = int(start)
        end = int(end)

        if end < start:
            raise ValueError("Endereço final menor que inicial")

        return start, (end - start + 1)

    return int(text), 1

def parse_bool(value):
    return str(value).strip().lower() == "true"

def colored_icon(path, color, icon_h=25, icon_w=25):
    renderer = QSvgRenderer(path)
    pixmap = QPixmap(QSize(icon_h, icon_w))
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.setCompositionMode (QPainter.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()

    return QIcon(pixmap)

def resource_path(*paths):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(BASE_DIR, *paths)