import os
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow
app=QApplication([])
w=MainWindow(); w.show()
w.chk_demo.setChecked(True)
w.btn_connect.click()
def check():
    print("connected:", w.connected, "| label:", w.lbl_conn.text())
    w.btn_estop.click()
    QTimer.singleShot(300, finish)
def finish():
    w._disconnect(); app.quit()
QTimer.singleShot(800, check)
app.exec()
print("BUTTON OK")
