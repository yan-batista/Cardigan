"""Colors and style tweaks shared by the widgets."""
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QProxyStyle, QStyle

# Colors of the "# project" and "## column" lines in the editor: (light theme, dark theme).
PROJECT_COLOR = ("#b45309", "#f5a65b")
COLUMN_COLOR = ("#0f6cbd", "#6cb6ff")
TAG_COLOR = ("#ea580c", "#ff9f43")


def mix(a, b, t):
    """The color t of the way from a to b."""
    return QColor(*(round(x + (y - x) * t) for x, y in
                    ((a.red(), b.red()), (a.green(), b.green()), (a.blue(), b.blue()))))


class NoAltMenuStyle(QProxyStyle):
    """Stops a lone Alt press from grabbing the menu bar: Alt+arrows are editor shortcuts."""

    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QStyle.SH_MenuBar_AltKeyNavigation:
            return 0
        return super().styleHint(hint, option, widget, returnData)
