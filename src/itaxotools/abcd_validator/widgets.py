from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from pathlib import Path

from .model import LogModel


class ElidedLineEdit(QtWidgets.QLineEdit):
    textDeleted = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextMargins(4, 0, 12, 0)
        self.setReadOnly(True)
        self.placeholder_text = "---"
        self.full_text = ""

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateElidedText()

    def focusInEvent(self, event):
        if self.full_text != self.placeholder_text:
            QtCore.QTimer.singleShot(0, self.selectAll)
        return super().focusInEvent(event)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if any(
            (
                event.key() == QtCore.Qt.Key_Backspace,
                event.key() == QtCore.Qt.Key_Delete,
            )
        ):
            self.textDeleted.emit()
        super().keyPressEvent(event)

    def setText(self, text: str):
        self.full_text = text
        self.updateElidedText()

    def text(self):
        return self.full_text

    def contextMenuEvent(self, event):
        pass

    def updateElidedText(self):
        metrics = QtGui.QFontMetrics(self.font())
        length = self.width() - self.textMargins().left() - self.textMargins().right() - 8
        elided_text = metrics.elidedText(self.full_text, QtCore.Qt.ElideLeft, length)
        QtWidgets.QLineEdit.setText(self, elided_text)

    def setPath(self, path: Path):
        text = str(path) if path != Path() else self.placeholder_text
        self.setText(text)


class BigPushButton(QtWidgets.QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = self.font()
        font.setPointSize(font.pointSize() * 1.20)
        font.setLetterSpacing(QtGui.QFont.AbsoluteSpacing, 1)
        self.setFont(font)

    def sizeHint(self):
        hint = super().sizeHint()
        return QtCore.QSize(hint.width(), hint.height() * 1.40)


class LogEntryDelegate(QtWidgets.QStyledItemDelegate):
    row_height = 20

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        painter.save()

        text_rect = QtCore.QRect(option.rect)
        text_rect -= QtCore.QMargins(6, 0, 6, 0)

        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

            text = index.data(QtCore.Qt.DisplayRole)

            pixmap = QtGui.QPixmap(text_rect.width(), text_rect.height())
            pixmap.fill(QtCore.Qt.transparent)

            pixmap_painter = QtGui.QPainter(pixmap)
            pixmap_painter.setRenderHint(QtGui.QPainter.Antialiasing)
            pixmap_painter.setPen(option.palette.light().color())
            pixmap_painter.setFont(painter.font())
            pixmap_painter.drawText(pixmap.rect(), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, text)
            pixmap_painter.end()

            pixmap = self.convert_pixmap_to_white(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.drawPixmap(text_rect, pixmap)

        else:
            painter.fillRect(option.rect, option.palette.base())
            painter.setPen(option.palette.text().color())

            text = index.data(QtCore.Qt.DisplayRole)

            painter.drawText(text_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, text)

        painter.restore()

    def sizeHint(self, option, index):
        text = index.data(QtCore.Qt.DisplayRole)
        metrics = QtGui.QFontMetrics(option.font)
        width = metrics.horizontalAdvance(text) + 24
        return QtCore.QSize(width, self.row_height)

    @staticmethod
    def convert_pixmap_to_white(pixmap: QtGui.QPixmap):
        image = pixmap.toImage()

        for y in range(image.height()):
            for x in range(image.width()):
                color = image.pixelColor(x, y)
                alpha = color.alpha()
                if alpha != 0:
                    color.setRgb(255, 255, 255)
                    color.setAlpha(alpha)
                    image.setPixelColor(x, y, color)

        return QtGui.QPixmap.fromImage(image)


class GrowingListView(QtWidgets.QListView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setItemDelegate(LogEntryDelegate(self))
        self.height_slack = 12
        self.lines_max = 12
        self.lines_min = 2
        self.max_width = 640

        font = self.font()
        font.setFamily("Courier New")
        self.setFont(font)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if any(
            (
                event.key() == QtCore.Qt.Key_Backspace,
                event.key() == QtCore.Qt.Key_Delete,
            )
        ):
            selected = self.selectionModel().selectedIndexes()
            if selected:
                indices = [index.row() for index in selected]
                self.requestDelete.emit(indices)
        super().keyPressEvent(event)

    def sizeHint(self):
        model = self.model()
        if not model:
            return super().sizeHint()

        width = 0
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            item_size_hint = self.sizeHintForIndex(index)
            width = max(width, item_size_hint.width())
        width = min(width, self.max_width)

        height = self.getHeightHint() + self.height_slack
        return QtCore.QSize(width, height)

    def getHeightHint(self):
        lines = self.model().rowCount() if self.model() else 0
        lines = max(lines, self.lines_min)
        lines = min(lines, self.lines_max)
        height = LogEntryDelegate.row_height
        return int(lines * height)

    def resizeEvent(self, event):
        self.setFixedWidth(self.sizeHint().width() + 24)
        self.setFixedHeight(self.sizeHint().height() + 24)


class SuccessDialog(QtWidgets.QMessageBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(f"{parent.title} - Success")
        self.setIcon(QtWidgets.QMessageBox.Information)
        self.setText("Validation against abcd-schema was successfull!")
        self.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.setOptions(QtWidgets.QMessageBox.Option.DontUseNativeDialog)


class FailureDialog(QtWidgets.QMessageBox):
    def __init__(self, parent, logs: LogModel):
        super().__init__(parent)
        self.setWindowTitle(f"{parent.title} - Failure")
        self.setIcon(QtWidgets.QMessageBox.Warning)
        self.setText("Problems were detected with the input files:")
        self.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Save)
        self.setOptions(QtWidgets.QMessageBox.Option.DontUseNativeDialog)

        self.list_view = GrowingListView()
        self.list_view.setModel(logs)

        layout: QtWidgets.QGridLayout = self.layout()
        layout.setVerticalSpacing(12)
        layout.setColumnMinimumWidth(2, 320)
        layout.addWidget(self.list_view, 1, 2)


class LongLabel(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextBrowserInteraction)
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.setStyleSheet("LongLabel {padding-left: 4px;}")
        self.setTextFormat(QtCore.Qt.RichText)
        self.setOpenExternalLinks(True)
        self.setWordWrap(True)

        action = QtGui.QAction("&Copy", self)
        action.triggered.connect(self.copy)
        self.addAction(action)

        action = QtGui.QAction(self)
        action.setSeparator(True)
        self.addAction(action)

        action = QtGui.QAction("Select &All", self)
        action.triggered.connect(self.select)
        self.addAction(action)

    def copy(self):
        text = self.selectedText()
        QtWidgets.QApplication.clipboard().setText(text)

    def select(self):
        self.setSelection(0, len(self.text()))
