from PySide6 import QtCore, QtGui

from itaxotools.common.resources import get_local
from itaxotools.common.widgets import VectorPixmap


def get_logo_pixmap() -> QtGui.QPixmap:
    return VectorPixmap(get_local(__package__, "resources/validator.svg"), QtCore.QSize(96, 96))


def get_logo_icon() -> QtGui.QIcon:
    return QtGui.QIcon(get_local(__package__, "resources/validator.ico"))
