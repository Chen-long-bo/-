import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow
import protocol
app = QApplication([])
w = MainWindow()
w.show()
w.chk_demo.setChecked(True)
w._connect()
def step1():
    print("connected:", w.connected)
    w._send(protocol.cmd_manual(0.2, 0.0, 0.0))
    QTimer.singleShot(800, step2)
def step2():
    print("mode:", w.lbl_mode.text())
    print("speed:", w.lbl_speed.text())
    print("batt:", w.lbl_batt.text())
    w._disconnect()
    app.quit()
QTimer.singleShot(800, step1)
app.exec()
print("DEMO OK")
