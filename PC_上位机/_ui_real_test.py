import os
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow
import protocol
app=QApplication([])
w=MainWindow()
w.show()
w.port_combo.setCurrentText("COM5")
w.baud_combo.setCurrentText("115200")
w._connect()
def step1():
    print("connected:",w.connected,"| mode:",w.lbl_mode.text(),"| batt:",w.lbl_batt.text(),"| speed:",w.lbl_speed.text())
    w.joy_y=0.5
    QTimer.singleShot(1200, step2)
def step2():
    print("after input | mode:",w.lbl_mode.text(),"| speed:",w.lbl_speed.text())
    w.joy_y=0.0
    QTimer.singleShot(500, step3)
def step3():
    w._send(protocol.cmd_stop_all())
    QTimer.singleShot(400, finish)
def finish():
    print("final | mode:",w.lbl_mode.text(),"| speed:",w.lbl_speed.text())
    w._disconnect()
    app.quit()
QTimer.singleShot(1200, step1)
app.exec()
print("UI REAL OK")
