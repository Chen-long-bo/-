import os
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow
import protocol
app=QApplication([])
w=MainWindow(); w.show()
w.port_combo.setCurrentText("COM5"); w.baud_combo.setCurrentText("115200")
w._connect()
def step1():
    print("connected",w.connected)
    w.joy_y=0.5
    QTimer.singleShot(2000, step2)
def step2():
    print("mode",w.lbl_mode.text(),"speed",w.lbl_speed.text())
    txt=w.log_view.toPlainText().splitlines()
    print("last logs:")
    for ln in txt[-8:]: print("  ",ln)
    w.joy_y=0.0
    w._send(protocol.cmd_stop_all())
    QTimer.singleShot(300, finish)
def finish():
    w._disconnect(); app.quit()
QTimer.singleShot(1200, step1)
app.exec()
print("DONE")
