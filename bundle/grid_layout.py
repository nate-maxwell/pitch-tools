"""
Grid Layout Wrapper

A thin wrapper around QtWidgets.QGridLayout that provides helpers to find
empty rows or columns and automatically place widgets or sublayouts.
"""


from typing import Union

from PySide6 import QtCore
from PySide6 import QtWidgets


QItem = Union[QtWidgets.QWidget, QtWidgets.QLayout]
ALIGN_TOP_LEFT = QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop


class GridLayout(QtWidgets.QGridLayout):
    """Enhanced QGridLayout with convenience methods for sequential placement
    and for finding empty rows or columns.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setHorizontalSpacing(4)
        self.setVerticalSpacing(4)

        # -----Absorb extra space to keep items in top left-----
        # God I hate front-end
        self.setRowStretch(9999, 1)
        self.setColumnStretch(9999, 1)

    # -----Query Methods-------------------------------------------------------

    def get_last_filled_row(self) -> int:
        """Return the last row index containing any items.

        Iterates over all layout items to determine the highest row index in
        use.

        Returns:
            int: The highest occupied row index, or -1 if the layout is empty.
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
        """Return the next empty column index in the given row.

        This inspects all items occupying the specified row and determines the
        first available (unused) column index.

        Args:
            row: The row number to search within.

        Returns:
            The first unoccupied column index in the given row.
        """
        occupied: set[int] = set()
        for i in range(self.count()):
            item_row, item_col, row_span, col_span = self.getItemPosition(i)
            if item_row <= row < item_row + row_span:
                occupied.update(range(item_col, item_col + col_span))
        for expected in range(max(occupied, default=-1) + 2):
            if expected not in occupied:
                return expected
        return 0

    # -----Insertion Methods---------------------------------------------------

    def _add_item(self, item: QItem, row: int, col: int) -> None:
        if isinstance(item, QtWidgets.QWidget):
            self.addWidget(item, row, col, ALIGN_TOP_LEFT)
        elif isinstance(item, QtWidgets.QLayout):
            self.addLayout(item, row, col, ALIGN_TOP_LEFT)

    def add_to_next_row(self, item: QItem) -> None:
        """Adds the QtWidget or QLayout item to the first column of the next
        row.
        """
        row = self.get_last_filled_row() + 1
        self._add_item(item, row, 0)

    def add_to_next_column(self, item: QItem) -> None:
        """Adds the QtWidget or QLayout item to the next empty column of the
        last occupied row.
        """
        row = self.get_last_filled_row()
        if row < 0:
            row = 0
        col = self.get_next_column(row)

        self._add_item(item, row, col)
