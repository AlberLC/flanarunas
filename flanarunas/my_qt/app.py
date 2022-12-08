import asyncio

from PySide6 import QtWidgets

from my_qt.combo_boxes import ComboSearch
from my_qt.windows import MyWindow


class MyQtApp(QtWidgets.QApplication):
    def __init__(self):
        super().__init__()

        self.setStyle('fusion')
        self.window = MyWindow()

    def connect_signals(self, controller):
        self.window.connect_signals(controller)

    def change_list_rune_pages_visibility(self):
        self.window.central_widget.change_list_rune_pages_visibility()

    @property
    def check_box_auto_selection(self) -> QtWidgets.QCheckBox:
        return self.window.central_widget.check_box_auto_selection

    @property
    def check_box_recommended_pages(self) -> QtWidgets.QCheckBox:
        return self.window.central_widget.check_box_recommended_pages

    @property
    def combo_search(self) -> ComboSearch:
        return self.window.central_widget.combo_search

    @property
    def list_rune_pages(self) -> QtWidgets.QListWidget:
        return self.window.central_widget.list_rune_pages

    def run(self):
        async def run():
            while True:
                self.processEvents()
                await asyncio.sleep(0)

        asyncio.create_task(run())

    def set_list_rune_pages_visibility(self, is_visible):
        self.window.central_widget.set_list_rune_pages_visibility(is_visible)
