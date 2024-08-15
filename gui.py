"""GUI entry point"""

from PySide6 import QtCore, QtGui, QtWidgets

import multiprocessing
from pathlib import Path
from typing import Callable

from itaxotools.common.bindings import Binder, Property, PropertyObject, PropertyRef


class Model(PropertyObject):
    measurement_file_path = Property(Path, Path())
    specimen_file_path = Property(Path, Path())
    multimedia_file_path = Property(Path, Path())
    multimedia_folder_path = Property(Path, Path())


class ElidedLineEdit(QtWidgets.QLineEdit):
    textDeleted = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
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
        length = self.width() - self.textMargins().left() - self.textMargins().right() - 16
        elided_text = metrics.elidedText(self.full_text, QtCore.Qt.ElideLeft, length)
        QtWidgets.QLineEdit.setText(self, elided_text)

    def setPath(self, path: Path):
        text = str(path) if path != Path() else self.placeholder_text
        self.setText(text)


class Main(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = "ABCD validator"
        self.resize(540, 0)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(self.title)

        self.model = Model()
        self.binder = Binder()

        layout = self.draw_input_fields()
        self.setLayout(layout)

    def draw_input_fields(self):
        layout = QtWidgets.QGridLayout()
        layout.setHorizontalSpacing(16)

        self.draw_input_field_row(
            layout, 0, "Measurement file", self.model.properties.measurement_file_path, self.show_file_dialog
        )
        self.draw_input_field_row(
            layout, 1, "Specimen file", self.model.properties.specimen_file_path, self.show_file_dialog
        )
        self.draw_input_field_row(
            layout, 2, "Multimedia file", self.model.properties.multimedia_file_path, self.show_file_dialog
        )
        self.draw_input_field_row(
            layout, 3, "Multimedia folder", self.model.properties.multimedia_folder_path, self.show_folder_dialog
        )

        return layout

    def draw_input_field_row(
        self, layout: QtWidgets.QGridLayout, row: int, text: str, property: PropertyRef, method: Callable
    ):
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


def run():
    app = QtWidgets.QApplication()

    main = Main()
    main.show()

    app.exec()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()
