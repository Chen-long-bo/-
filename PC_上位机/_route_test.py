import os
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow
app=QApplication([])
w=MainWindow(); w.show()
w.chk_demo.setChecked(True)
w.btn_connect.click()
def start():
    w.spin_route.setValue(100)
    w.spin_route_speed.setValue(1.0)
    w.btn_route_start.click()
    print("route active:", w.route_active, "| progress:", w.lbl_route_progress.text())
    QTimer.singleShot(1800, check)
def check():
    txt=w.log_view.toPlainText()
    print("manual frame:", "AA 55 07 01" in txt)
    print("rotate frame:", "AA 55 03 0D" in txt)
    print("progress:", w.lbl_route_progress.text())
    w.btn_route_stop.click()
    QTimer.singleShot(300, finish)
def finish():
    print("stopped, active:", w.route_active, "| progress:", w.lbl_route_progress.text())
    w._disconnect(); app.quit()
QTimer.singleShot(700, start)
app.exec()
print("ROUTE TEST OK")
