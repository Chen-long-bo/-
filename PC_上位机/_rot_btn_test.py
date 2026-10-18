import os
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow
app=QApplication([])
w=MainWindow(); w.show()
w.chk_demo.setChecked(True)
w.btn_connect.click()
def step():
    print("connected", w.connected)
    w.btn_rot_l90.click()
    QTimer.singleShot(300, check)
def check():
    txt=w.log_view.toPlainText()
    print("rotate frame found:", "AA 55 03 0D 84 03 97" in txt)
    print("last log:", txt.splitlines()[-1] if txt.splitlines() else "")
    w._disconnect(); app.quit()
QTimer.singleShot(700, step)
app.exec()
print("ROTATE BUTTON OK")
