import re
from typing import Iterable

from PySide6 import QtCore, QtGui, QtWidgets

from models.rune_page import RunePage
from my_qt import ui_loader
from my_qt.combo_boxes import ComboSearch


class ListRunePages(QtWidgets.QListWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.controller = None
        self.action_delete = QtGui.QAction('Eliminar')
        self.action_duplicate = QtGui.QAction('Duplicar')
        self.delete_shortcut = QtGui.QShortcut(QtGui.QKeySequence.Delete, self)
        self.action_delete.setShortcut(QtGui.QKeySequence.Delete)
        self.delete_shortcut.activated.connect(self.delete_selected_items)
        self.action_delete.triggered.connect(self.delete_selected_items)
        self.action_duplicate.triggered.connect(self.duplicate_selected_items)
        self.menu = QtWidgets.QMenu()
        self.menu.addAction(self.action_duplicate)
        self.menu.addSeparator()
        self.menu.addAction(self.action_delete)

    def connect_signals(self, controller):
        self.controller = controller
        self.itemChanged.connect(self.on_item_changed)

    def _auto_rename_item(self, item: QtWidgets.QListWidgetItem):
        def get_suffix_number(text: str) -> int:
            try:
                return int(re.findall(r'(_\d+)+', text)[0].strip('_'))
            except IndexError:
                return 0

        item_names = [item_.data_.name for item_ in self.items_]
        next_suffix_number = max(get_suffix_number(item_name) for item_name in item_names) + 1
        if item.data_.name in item_names:
            if get_suffix_number(item.data_.name):
                item.data_.name = re.sub(r'(_\d+)+', '', item.data_.name)
            item.data_.name = f'{item.data_.name}_{next_suffix_number}'
            item.setText(item.data_.name)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        if not self.selectedItems():
            return

        self.menu.exec(event.globalPos())

    def delete_selected_items(self):
        if not self.selectedItems():
            return

        message_box = QtWidgets.QMessageBox(parent=self)
        message_box.setIcon(QtWidgets.QMessageBox.Warning)
        message_box.setWindowTitle('Eliminar')
        message_box.setText('¿Estás seguro?')
        message_box.setIcon(QtWidgets.QMessageBox.Warning)
        message_box.addButton('Aceptar', QtWidgets.QMessageBox.AcceptRole)
        message_box.addButton('Cancelar', QtWidgets.QMessageBox.RejectRole)
        if message_box.exec():
            return

        for item in self.selectedItems():
            self.takeItem(self.row(item))

        self.controller.update_runes()

    def dropEvent(self, event: QtGui.QDropEvent):
        super().dropEvent(event)
        self.controller.update_runes()

    def duplicate_selected_items(self):
        for item in self.selectedItems():
            new_item = item.clone()
            new_item.data_ = item.data_.deep_copy()
            self._auto_rename_item(new_item)
            self.insertItem(self.row(item) + 1, new_item)

        self.controller.update_runes()

    @property
    def items_(self) -> list[QtWidgets.QListWidgetItem]:
        return [self.item(i) for i in range(self.count())]

    @items_.setter
    def items_(self, rune_pages: Iterable[RunePage]):
        self.clear()
        for rune_page in rune_pages:
            item = QtWidgets.QListWidgetItem(rune_page.name)
            item.data_ = rune_page
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self.addItem(item)

    def on_item_changed(self, item: QtWidgets.QListWidgetItem):
        item.data_.name = item.text()
        self.blockSignals(True)
        item.setText(item.data_.name)
        self.blockSignals(False)

        self.controller.update_runes()


class MyCentralWidget(QtWidgets.QWidget):
    widget_rune_pages: QtWidgets.QWidget
    label_rune_pages: QtWidgets.QLabel
    button_show: QtWidgets.QPushButton
    check_box_auto_selection: QtWidgets.QCheckBox
    check_box_recommended_pages: QtWidgets.QCheckBox
    combo_search: ComboSearch
    list_rune_pages: ListRunePages

    def __init__(self, parent):
        super().__init__(parent)
        self.controller = None
        ui_loader.load_ui('resources/central_widget.ui', self, [ComboSearch, ListRunePages])

        self.set_list_rune_pages_visibility(False)

    def connect_signals(self, controller):
        self.controller = controller

        self.list_rune_pages.connect_signals(controller)

        self.button_show.clicked.connect(self.change_list_rune_pages_visibility)
        # noinspection PyUnresolvedReferences
        self.button_show.clicked.connect(self.window().resize_, QtCore.Qt.QueuedConnection)

        self.check_box_auto_selection.stateChanged.connect(controller.save_data)
        self.check_box_recommended_pages.stateChanged.connect(controller.save_data)

        self.combo_search.currentTextChanged.connect(controller.on_current_text_changed)

    def change_list_rune_pages_visibility(self):
        self.set_list_rune_pages_visibility(not self.widget_rune_pages.isVisible())

    def set_list_rune_pages_visibility(self, is_visible):
        self.widget_rune_pages.setVisible(is_visible)

        if is_visible:
            self.button_show.setText('🠕🠕🠕 Ocultar 🠕🠕🠕')
        else:
            self.button_show.setText('🠗🠗🠗 Páginas de runas 🠗🠗🠗')

        if self.controller:
            self.controller.save_data()
