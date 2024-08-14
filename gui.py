"""GUI entry point"""

from PySide6 import QtCore, QtWidgets

import multiprocessing


class Main(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlags(QtCore.Qt.Window)
        self.title = "ABCD validator"


def run():
    app = QtWidgets.QApplication()

    main = Main()
    main.show()

    app.exec()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()
