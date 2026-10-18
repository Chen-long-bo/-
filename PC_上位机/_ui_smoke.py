import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow
app = QApplication([])
w = MainWindow()
w.show()
QTimer.singleShot(1500, app.quit)
app.exec()
print("UI OK")
