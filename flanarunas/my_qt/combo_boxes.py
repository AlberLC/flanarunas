from PySide6 import QtCore, QtGui, QtWidgets


class ComboSearch(QtWidgets.QComboBox):
    # noinspection PyUnresolvedReferences
    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self._items = items or []
        font = QtGui.QFont()
        font.setPointSize(14)

        self.setFont(font)
        self.lineEdit().setFont(font)
        self.completer = QtWidgets.QCompleter([])
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)
        # noinspection PyTypeChecker
        self.completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        self.completer.popup().setFont(font)
        self.setCompleter(self.completer)

        self._is_item_highlighted = False

        self.lineEdit().textEdited.connect(self._set_completer_items)
        self.lineEdit().returnPressed.disconnect()  # no add new elements at enter
        self.completer.popup().activated.connect(lambda x: print(1, x))

    def add_item(self, item: str):
        self.items += [item]

    def delete_item(self, name: str):
        self._items.remove(name)
        self.items = self._items

    def event(self, event: QtCore.QEvent) -> bool:
        if isinstance(event, QtGui.QKeyEvent) and event.key() == QtCore.Qt.Key_Tab and event.type() == QtCore.QEvent.KeyPress:
            # noinspection PyUnresolvedReferences
            self.completer.activated.emit(self.completer.popup().model().data(self.completer.popup().currentIndex()))
            self.setFocus()

        return super().event(event)

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        self.blockSignals(True)
        text = self.lineEdit().text()
        self.clear()
        self._items = sorted(items)
        self.addItems(self.items)
        self.lineEdit().setText(text)
        self.blockSignals(False)

    def setCurrentText(self, item):
        super().setCurrentText(item if item else '')
        # self._set_cursor_start()

    def _set_completer_items(self):
        items = self.items.copy()
        items = [item for item in items if self.currentText().lower() in item.lower()]
        self.completer.model().setStringList(items)

    # def _set_cursor_start(self):
    #     self.lineEdit().setCursorPosition(0)
