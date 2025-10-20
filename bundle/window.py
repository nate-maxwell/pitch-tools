"""
# Bundle Window

* Description:

    The primary bundle PySide window.
"""


from pathlib import Path
from typing import Callable

from PySide6 import QtGui
from PySide6 import QtWidgets

import bundle.text_kind
from bundle.grid_layout import GridLayout


drop_func_signature = Callable[[str], None]
"""The signature a bundle drop function should use.
The drop function is what the bundle passes the dropped text to for execution.
"""

multi_line_types = (
    bundle.text_kind.TextKind.FILE_PATHS,
    bundle.text_kind.TextKind.MAYA_DAG_PATHS
)
"""Kinds of text in entries can exist on multiple lines.
Something like python code is a string block that can span multiple lines but
is a single entry, so it would not count.
"""


class BundleButton(QtWidgets.QWidget):
    """
    A bundle button, used to store items and a selection function within the
    bundle menu.
    """

    def __init__(
            self,
            entries: list[str],
            icon: Path,
            action: Callable[[list[str]], None]
    ) -> None:
        super().__init__()

        self.setToolTip('\n'.join(entries))
        self.setFixedSize(40, 40)

        self.icon_path = icon
        self.action = action
        self.entries = entries

        self.layout_main = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout_main)

        self.button = QtWidgets.QPushButton()
        self.layout_main.addWidget(self.button)
        self.set_icon(icon)
        self.button.clicked.connect(self.button_connection)

    def set_icon(self, icon_path: Path) -> None:
        pixmap: QtGui.QPixmap = QtGui.QPixmap(icon_path.as_posix())
        self.button.setIcon(QtGui.QIcon(pixmap))

    def button_connection(self) -> None:
        self.action(self.entries)


class BundleWindow(QtWidgets.QMainWindow):
    """
    The parent Bundle window for creating, storing, and recalling bundle
    selections.
    """

    def __init__(
            self,
            button_factory: Callable[[str], BundleButton],
            parent: QtWidgets.QMainWindow = None
    ) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setWindowTitle('bundle')

        self.button_factory = button_factory

        self._max_col = 10
        self._cur_col = 0

        w = (self._max_col * 40) + (4 * self._max_col)
        h = (self._max_col * 40) + (4 * self._max_col)
        self.setFixedSize(w, h)

        self._create_widgets()
        self._create_layout()

    def _create_widgets(self) -> None:
        self.widget_main = QtWidgets.QWidget()
        self.layout_main = GridLayout()

    def _create_layout(self) -> None:
        self.setCentralWidget(self.widget_main)
        self.widget_main.setLayout(self.layout_main)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if not event.mimeData().hasText():
            event.ignore()
            return

        event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if not event.mimeData().hasText():
            event.ignore()
            return

        text = event.mimeData().text()
        button = self.button_factory(text)
        if button is None:
            print('button was None')
            return

        if self._cur_col >= self._max_col:
            self._cur_col = 0
            self.layout_main.add_to_next_row(button)
        else:
            self.layout_main.add_to_next_column(button)
            self._cur_col += 1

        event.acceptProposedAction()
