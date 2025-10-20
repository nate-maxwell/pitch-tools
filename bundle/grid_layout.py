"""
# Grid Layout Wrapper

* Description:

    A wrapper for QtWidgets.QGridLayout that finds empty slots in rows and
    columns.
"""


from typing import Union

from PySide6 import QtCore
from PySide6 import QtWidgets


q_item = Union[QtWidgets.QWidget, QtWidgets.QLayout]


class GridLayout(QtWidgets.QGridLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setHorizontalSpacing(4)
        self.setVerticalSpacing(4)

        # -----Absorb extra space to keep items in top left-----
        # God I hate front-end
        self.setRowStretch(9999, 1)
        self.setColumnStretch(9999, 1)

    def get_last_filled_row(self) -> int:
        """Return the last row index that contains any items in the QGridLayout.

        This inspects all items in the layout and returns the highest row index
        occupied by any widget or layout item. If the layout is empty, returns
        -1.

        Returns:
            The last (highest) row index that has any items, or -1 if none
             exist.
        """
        if self.count() == 0:
            return -1

        last_row: int = -1

        for i in range(self.count()):
            row, _col, row_span, _col_span = self.getItemPosition(i)
            bottom_row = row + (row_span - 1 if row_span > 0 else 0)
            if bottom_row > last_row:
                last_row = bottom_row

        return last_row

    def get_next_column(self, row: int) -> int:
        """Return the next empty column index in the given row of a
        QGridLayout.

        This inspects all items occupying the specified row and determines the
        first available (unused) column index.

        Args:
            row: The row number to search within.

        Returns:
            The first unoccupied column index in the given row.
        """
        if self is None or self.count() == 0:
            return 0

        occupied_columns: list[int] = []

        for i in range(self.count()):
            item_row, item_col, row_span, col_span = self.getItemPosition(i)
            if item_row <= row < item_row + row_span:
                for c in range(item_col, item_col + col_span):
                    if c not in occupied_columns:
                        occupied_columns.append(c)

        if not occupied_columns:
            return 0

        occupied_columns.sort()

        expected_col = 0
        for c in occupied_columns:
            if c != expected_col:
                return expected_col
            expected_col += 1

        return expected_col

    def _add_item(self, item: q_item, row: int, col: int) -> None:
        # Always align the item to the top-left of its cell
        if isinstance(item, QtWidgets.QWidget):
            self.addWidget(item, row, col,
                           QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        elif isinstance(item, QtWidgets.QLayout):
            self.addLayout(item, row, col,
                           QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

    def add_to_next_row(self, item: q_item) -> None:
        """Adds the QtWidget or QLayout item to the first column of the next
        row.
        """
        row = self.get_last_filled_row() + 1
        self._add_item(item, row, 0)

    def add_to_next_column(self, item: q_item) -> None:
        """Adds the QtWidget or QLayout item to the next empty column of the
        last occupied row.
        """
        row = self.get_last_filled_row()
        if row < 0:
            row = 0
        col = self.get_next_column(row)

        self._add_item(item, row, col)
