import os
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow
app=QApplication([])
w=MainWindow(); w.show()
w.chk_demo.setChecked(True); w.btn_connect.click()
w.spin_route.setValue(100)
w.spin_route_speed.setValue(1.0)
w.spin_route_pause.setValue(200)
def start():
    w.btn_route_start.click()
    print("t0:", w.lbl_route_progress.text())
    QTimer.singleShot(1000, t1)
def t1():
    print("t1s:", w.lbl_route_progress.text())
    QTimer.singleShot(2500, t2)
def t2():
    print("t3.5s:", w.lbl_route_progress.text())
    w.btn_route_stop.click()
    QTimer.singleShot(300, finish)
def finish():
    print("stopped:", w.lbl_route_progress.text())
    w._disconnect(); app.quit()
QTimer.singleShot(700, start)
app.exec()
print("ROUTE TIMING OK")
