from __future__ import annotations

from PySide6 import QtCore

from pathlib import Path

from abcd_converter_gfbio_org.abcd_conversion import convert_csv_to_abcd
from abcd_converter_gfbio_org.handlers import InOutHandler, Outputter

from itaxotools.common.bindings import Binder, Property, PropertyObject

from .types import ListLogger, LogEntry, LogType


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
