from PyQt5 import QtWidgets
from qiwugrader.view.config_file_view import Ui_Dialog


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    widget = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(widget)
    widget.show()
    sys.exit(app.exec_())
