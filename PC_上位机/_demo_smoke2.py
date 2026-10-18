import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow
app = QApplication([])
w = MainWindow()
w.show()
w.chk_demo.setChecked(True)
w._connect()
def step1():
    print("connected:", w.connected)
    w.joy_y = 0.5          # 摇杆向前50%
    QTimer.singleShot(1000, step2)
def step2():
    print("mode:", w.lbl_mode.text())
    print("speed:", w.lbl_speed.text())
    print("batt:", w.lbl_batt.text())
    w.joy_y = 0.0
    w._disconnect()
    app.quit()
QTimer.singleShot(600, step1)
app.exec()
print("DEMO OK")
