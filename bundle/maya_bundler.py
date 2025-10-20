"""
# Example Maya Bundle Window

* Description:

    A demo of how the bundler can be used inside of maya.
"""


import subprocess
import sys
from pathlib import Path
from typing import Optional
from typing import cast

import maya.OpenMayaUI as omui
import shiboken6
from PySide6 import QtWidgets
from maya import cmds

import bundle.text_kind
import bundle.window


icons_dir = Path(Path(__file__).parent, 'icons')
icons: dict[str, Path] = {
    'python': Path(icons_dir, 'icon_python.png'),
    'folder': Path(icons_dir, 'icon_folder.png'),
    'object': Path(icons_dir, 'icon_object.png')
}


# -----Maya Helpers------------------------------------------------------------


class UndoChunk:
    """Context manager for a Maya undoChunk.

    Everything under the `with` statement will be grouped into a single undo
    action. This is similar to pymel's `pymel.core.system.UndoChunk`, with the
    exception that this implementation forces you to provide an undo name.

    Examples:
        >>> with UndoChunk('Duplicate and mirror'):
        >>>     # Everything here will be part of a single undoChunk
        >>>     ...
        >>>
    """

    def __init__(self, chunk_name: str) -> None:
        self.chunk_name = chunk_name

    def __enter__(self) -> None:
        cmds.undoInfo(openChunk=True, chunkName=self.chunk_name)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        cmds.undoInfo(closeChunk=True)


def get_main_window() -> QtWidgets.QMainWindow:
    """Get the Maya main window as a QMainWindow instance."""
    win = shiboken6.wrapInstance(
        int(omui.MQtUtil.mainWindow()), QtWidgets.QMainWindow
    )
    return cast(QtWidgets.QMainWindow, win)


# -----Action Functions--------------------------------------------------------


def dag_action(items: list[str]) -> None:
    cmds.select(clear=True)
    if items:
        cmds.select(items, add=True)


def script_action(items: list[str]) -> None:
    exec(items[0])


def file_action(items: list[str]) -> None:
    min_items = list(set(items))
    for i in min_items:
        subprocess.run(['explorer', '/select,', i])


# -----Maya Wrapper------------------------------------------------------------


def button_factory(s: str) -> Optional[bundle.window.BundleButton]:
    """Generates a button given the dragged and dropped text s."""
    text_kind = bundle.text_kind.classify_text(s)

    icon = None
    entries = None
    action = None

    if text_kind == bundle.text_kind.TextKind.FILE_PATHS:
        icon = icons['folder']
        entries = s.split('\n')
        action = file_action
    if text_kind == bundle.text_kind.TextKind.PYTHON_SCRIPT:
        print('$$$$$$$$$$$$$$$$$$$$$$$$')
        icon = icons['python']
        entries = [s]
        action = script_action
    if text_kind == bundle.text_kind.TextKind.MAYA_DAG_PATHS:
        icon = icons['object']
        entries = s.split('\n')
        action = dag_action

    if icon is None and entries is None and action is None:
        return None

    button = bundle.window.BundleButton(
        entries=entries,
        icon=icon,
        action=action
    )

    return button


_WIN: Optional[bundle.window.BundleWindow] = None


def main() -> int:
    app = QtWidgets.QApplication.instance()
    created_app = False
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        created_app = True

    global _WIN
    if _WIN is None:
        _WIN = bundle.window.BundleWindow(button_factory, get_main_window())

    _WIN.show()
    _WIN.raise_()
    _WIN.activateWindow()

    if created_app:
        return app.exec()
    return 0


if __name__ == '__main__':
    sys.exit(main())
