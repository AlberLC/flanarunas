import sys

from PySide6 import QtCore, QtGui, QtWidgets

from my_qt.widgets import MyCentralWidget


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = None

        self.icon = QtGui.QIcon('resources/logo.png')
        self.setWindowTitle('FlanaRunas')
        self.setWindowIcon(self.icon)

        self.central_widget = MyCentralWidget(self)
        self.setCentralWidget(self.central_widget)

        self.show()

    def connect_signals(self, controller):
        self.controller = controller

        self.central_widget.connect_signals(controller)

    def closeEvent(self, event) -> None:
        super().closeEvent(event)
        sys.exit()

    def enterEvent(self, event: QtGui.QEnterEvent):
        super().enterEvent(event)

        if self.controller.current_champion:
            selected_rune_pages = self.controller.saved_rune_pages.get(self.controller.current_champion.id, [])
            self.central_widget.list_rune_pages.items_ = selected_rune_pages
        else:
            self.central_widget.list_rune_pages.clear()

    def resize_(self):
        width = self.width()
        self.adjustSize()
        self.resize(width, self.height())

    def sizeHint(self):
        return QtCore.QSize(250, 100)
