import PySide2

from PySide2.QtCore import Signal
from PySide2.QtWidgets import *


class ClickableLineEdit(QLineEdit):
    clicked = Signal()

    def __init__(self, default_value):
        super(ClickableLineEdit, self).__init__(default_value)
        self.default_value = default_value

    def mousePressEvent(self, arg__1: PySide2.QtGui.QMouseEvent):
        super(ClickableLineEdit, self).mousePressEvent(arg__1)
        self.clicked.emit()