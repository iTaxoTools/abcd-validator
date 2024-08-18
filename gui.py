from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

import argparse
import multiprocessing
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Callable

from abcd_converter_gfbio_org.abcd_conversion import convert_csv_to_abcd
from abcd_converter_gfbio_org.handlers import InOutHandler, Outputter

import skin
from itaxotools.common.bindings import Binder, Property, PropertyObject, PropertyRef


class LogType(Enum):
    Warning = auto()
    Error = auto()


@dataclass
class LogEntry:
    type: LogType
    text: str

    def __str__(self):
        prefix = {
            LogType.Warning: "\u2757",
            LogType.Error: "\u274C",
        }[self.type]
        return f"{prefix} {self.text}"


class ListLogger(Outputter):
    def __init__(self, reference: list[LogEntry], type: LogType):
        self.reference = reference
        self.type = type

    def handle(self, description, content):
        entry = LogEntry(self.type, str(description))
        self.reference.append(entry)


class LogModel(QtCore.QAbstractListModel):
    def __init__(self):
        super().__init__()
        self.logs: list[LogEntry] = []

    def set_logs(self, logs: list[LogEntry]):
        self.beginResetModel()
        self.logs = logs
        self.endResetModel()

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            entry = self.logs[index.row()]
            return str(entry)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.logs)

    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled


class Worker(QtCore.QThread):
    finished = QtCore.Signal(list)

    def __init__(self, model: Model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model

        app = QtCore.QCoreApplication.instance()
        app.aboutToQuit.connect(self.terminate)

    def run(self):
        logs: list[str] = []

        io_handler = InOutHandler(verbose=False, out_file="result.xml", file_directory=str(self.model.multimedia_folder_path.resolve()))
        io_handler.resultFileHandler = Outputter()
        io_handler.warning_handler = ListLogger(logs, LogType.Warning)
        io_handler.errorHandler = ListLogger(logs, LogType.Error)
        io_handler.logHandler = Outputter()

        convert_csv_to_abcd(
            str(self.model.specimen_file_path.resolve()),
            str(self.model.measurement_file_path.resolve()),
            str(self.model.multimedia_file_path.resolve()),
            io_handler,
        )

        self.finished.emit(logs)


class Model(PropertyObject):
    logs = QtCore.Signal(list)

    measurement_file_path = Property(Path, Path())
    specimen_file_path = Property(Path, Path())
    multimedia_file_path = Property(Path, Path())
    multimedia_folder_path = Property(Path, Path())

    ready = Property(bool, False)
    busy = Property(bool, False)

    def __init__(self, args: dict):
        super().__init__()
        self.set_properties_from_dict(args)
        self.binder = Binder()
        self.binder.bind(self.properties.multimedia_file_path, self.propagate_multimedia_path)
        for property in self.properties:
            self.binder.bind(property, self.update_ready)

        self.worker = Worker(self)
        self.worker.finished.connect(self.on_done)

    def set_properties_from_dict(self, args):
        for k, v in args.items():
            self.properties[k].set(Path(v).resolve())

    def check_ready(self):
        for path in [
            self.measurement_file_path,
            self.specimen_file_path,
            self.multimedia_file_path,
            self.multimedia_folder_path,
        ]:
            if path == Path():
                return False
        return True

    def update_ready(self):
        self.ready = self.check_ready()

    def propagate_multimedia_path(self, path: Path):
        if path != Path():
            self.multimedia_folder_path = path.parent

    def start(self):
        self.busy = True
        self.worker.start()

    def on_done(self, logs: list):
        self.busy = False
        self.logs.emit(logs)


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
    def __init__(self, parent: Main):
        super().__init__(parent)
        self.setWindowTitle(parent.title)
        self.setIcon(QtWidgets.QMessageBox.Information)
        self.setText("Validation against abcd-schema was successfull!")
        self.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.setOptions(QtWidgets.QMessageBox.Option.DontUseNativeDialog)


class FailureDialog(QtWidgets.QMessageBox):
    def __init__(self, parent: Main, logs: LogModel):
        super().__init__(parent)
        self.setWindowTitle(parent.title)
        self.setIcon(QtWidgets.QMessageBox.Warning)
        self.setText("Problems were detected with the input files:")
        self.setStandardButtons(QtWidgets.QMessageBox.Ok)
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


class Main(QtWidgets.QWidget):
    def __init__(self, args: dict):
        super().__init__()
        self.title = "ABCD validator"
        self.resize(560, 0)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(self.title)

        self.model = Model(args)
        self.logs = LogModel()
        self.binder = Binder()
        self.success_dialog = SuccessDialog(self)
        self.failure_dialog = FailureDialog(self, self.logs)

        label = LongLabel(
            "Test whether your tables with specimen-based taxonomic data "
            "and associated files are correctly structured and named to be "
            "uploaded to a repository. "
            "Table column headers will be checked against the standards of "
            "ABCD (Access to Biological Collections Data). "
            "<br><br>"
            "Read more about the ABCD schema here: "
            '<a href="https://abcd.tdwg.org">https://abcd.tdwg.org</a>'
        )
        fields = self.draw_input_fields()
        validate = BigPushButton("VALIDATE")

        self.binder.bind(self.model.properties.ready, validate.setEnabled)
        self.binder.bind(self.model.properties.busy, self.set_busy)
        self.binder.bind(self.model.logs, self.report_logs)
        self.binder.bind(validate.clicked, self.model.start)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(label)
        layout.addLayout(fields)
        layout.addWidget(validate)
        self.setLayout(layout)

        self.setFixedHeight(self.sizeHint().height())
        self.setMinimumWidth(self.sizeHint().width() + 100)

    def draw_input_fields(self):
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(8)

        properties = self.model.properties
        self.draw_input_field_row(layout, 0, "Specimen table", properties.specimen_file_path, self.show_file_dialog)
        self.draw_input_field_row(layout, 1, "Measurement table", properties.measurement_file_path, self.show_file_dialog)
        self.draw_input_field_row(layout, 2, "Multimedia file table", properties.multimedia_file_path, self.show_file_dialog)
        self.draw_input_field_row(layout, 3, "Folder with multimedia files", properties.multimedia_folder_path, self.show_folder_dialog)

        return layout

    def draw_input_field_row(self, layout: QtWidgets.QGridLayout, row: int, text: str, property: PropertyRef, method: Callable):
        label = QtWidgets.QLabel(text + ":")
        field = ElidedLineEdit()
        button = QtWidgets.QPushButton("Browse")
        self.binder.bind(button.clicked, lambda: method(property))
        self.binder.bind(field.textDeleted, lambda: property.set(Path()))
        self.binder.bind(property, field.setPath)
        layout.addWidget(label, row, 0)
        layout.addWidget(field, row, 1)
        layout.addWidget(button, row, 2)

    def show_file_dialog(self, property: PropertyRef):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self.window(),
            caption=f"{self.title} - Browse file",
        )
        if not filename:
            return
        property.set(Path(filename))

    def show_folder_dialog(self, property: PropertyRef):
        filename = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self.window(),
            caption=f"{self.title} - Browse file",
        )
        if not filename:
            return
        property.set(Path(filename))

    def set_busy(self, busy: bool):
        self.setEnabled(not busy)
        if busy:
            cursor = QtGui.QCursor(QtCore.Qt.BusyCursor)
            QtWidgets.QApplication.setOverrideCursor(cursor)
        else:
            QtWidgets.QApplication.restoreOverrideCursor()

    def report_logs(self, logs: list[LogEntry]):
        if not logs:
            self.success_dialog.exec()
        else:
            self.logs.set_logs(logs)
            self.failure_dialog.exec()


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--measurement_file", "-m", type=str)
    parser.add_argument("--specimen_file", "-s", type=str)
    parser.add_argument("--multimedia_file", "-x", type=str)
    parser.add_argument("--multimedia_folder", "-f", type=str)
    args = parser.parse_args()

    return {f"{k}_path": v for k, v in vars(args).items() if v is not None}


def run():
    app = QtWidgets.QApplication()
    skin.apply(app)

    args = parse_args()

    main = Main(args)
    main.show()

    app.exec()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()
