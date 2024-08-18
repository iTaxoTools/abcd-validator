from PySide6 import QtWidgets

import argparse

from . import skin
from .view import Main


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--measurement_file", "-m", type=str)
    parser.add_argument("--specimen_file", "-s", type=str)
    parser.add_argument("--multimedia_file", "-x", type=str)
    parser.add_argument("--multimedia_folder", "-f", type=str)
    args = parser.parse_args()

    return {f"{k}_path": v for k, v in vars(args).items() if v is not None}


def run(args={}):
    app = QtWidgets.QApplication()
    skin.apply(app)

    args = args or parse_args()
    main = Main(args)
    main.show()

    app.exec()
