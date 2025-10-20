"""
String Looks Like

A collection of regular expressions to see if a string resembles any kind
of known expression.
"""


import ast
import enum
import re
from pathlib import Path


class TextKind(enum.Enum):
    """Kinds of text the classifiers can detect."""
    MAYA_DAG_PATHS = 'maya_dag_paths'
    FILE_PATHS = 'file_paths'
    PYTHON_SCRIPT = 'python_script'
    UNKNOWN = 'unknown'


def split_nonempty_lines(text: str) -> list[str]:
    """Split text into non-empty, stripped lines."""
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _looks_like_windows_drive_path(line: str) -> bool:
    """
    Returns whether line looks like C:\folder\file.txt or C:/folder/file.txt.
    Args:
        line (string): The string to match.
    Returns:
        bool: Does path resemble windows drive path?
    """
    return re.match(r'^[A-Za-z]:[\\/]', line) is not None


def _looks_like_posix_path(line: str) -> bool:
    """
    Returns whether line looks like /home/user/file or ./file or ../file
    Args:
        line (string): The string to match.
    Returns:
        bool: Does path resemble posix path?
    """
    if line.startswith('/'):
        return True
    if line.startswith('./') or line.startswith('../'):
        return True
    return False


def _looks_like_unc_path(line: str) -> bool:
    # e.g. \\server\share\path or //server/share/path
    return re.match(r'^(?:\\\\|//)[^\\/\s]+[\\/]?', line) is not None


def _has_pathlike_separators(line: str) -> bool:
    return ('\\' in line) or ('/' in line)


def looks_like_file_path(line: str) -> bool:
    """Heuristic for a single filesystem path.
    Args:
        line (str): The text to validate.
    Returns:
        bool: Whether the line looks like an unc, posix, windows path, or some
         other file system path type.
    """
    if not _has_pathlike_separators(line):
        return False

    if _looks_like_windows_drive_path(line):
        return True
    if _looks_like_unc_path(line):
        return True
    if _looks_like_posix_path(line):
        return True

    # Fallback: if it normalizes to something non-trivial with pathlib, treat
    # as path
    try:
        p = Path(line)
        # Reject pure filename with no separators to avoid false positives
        if p.name != line and len(str(p)) > 1:
            return True
    except (OSError, RuntimeError, ValueError):
        pass

    return False


def looks_like_python_script(text: str) -> bool:
    """True if the text parses cleanly as Python (non-empty)."""
    # Avoid parsing a long list of paths as code: require at least one newline
    # or a semicolon/colon/def/class/import to hint code-ish content.
    trimmed = text.strip()
    if not trimmed:
        return False

    tokens = (
        '\n', ';', ':', 'def ', 'class ',
        'import ', 'from ', 'with ', 'for ', 'if '
    )
    code_hint = any(tok in trimmed for tok in tokens)

    try:
        ast.parse(trimmed)
        return code_hint or '\n' in trimmed or len(trimmed.split()) > 3
    except SyntaxError:
        return False


_MAYA_SEGMENT_RX = r'[A-Za-z0-9_][A-Za-z0-9_:]*'
_MAYA_PATH_RX = re.compile(rf'^\|?({_MAYA_SEGMENT_RX})(?:\|{_MAYA_SEGMENT_RX})*$')


def looks_like_maya_dag_path(line: str) -> bool:
    """Heuristic for a single Maya DAG path (absolute or relative).

    Accepts patterns like:
      - |pCube1
      - |group1|pSphere1
      - group1|pSphere1
      - ns:grp|ns:meshShape1

    Rules:
      - One or more segments separated by '|'
      - Absolute may start with leading '|'
      - Each segment must start with an alnum or underscore, and may contain
        alnum, underscore, or ':' (namespace). No spaces in segments.

    This is intentionally conservative to avoid false positives.
    """
    if looks_like_file_path(line):
        return False
    if ' ' in line or '\t' in line:
        return False

    return _MAYA_PATH_RX.match(line) is not None


def classify_text(text: str) -> TextKind:
    """
    Classifies the given text string based on what kind of pattern it matches.
    Assumes all lines are of the same type.

    Args:
        text (str): The text to classify.
    Returns:
        TextKind: The text kind enum entry.
         Returns TextKind.UNKNOWN if text could not be classified.
    """
    if looks_like_python_script(text):
        return TextKind.PYTHON_SCRIPT

    lines = split_nonempty_lines(text)

    if looks_like_file_path(lines[0]):
        return TextKind.FILE_PATHS
    if looks_like_maya_dag_path(lines[0]):
        return TextKind.MAYA_DAG_PATHS

    return TextKind.UNKNOWN
