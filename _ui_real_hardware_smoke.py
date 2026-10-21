import sys, time, traceback
from pathlib import Path
sys.path.insert(0, str(Path('PC_上位机').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from ui.main_window import MainWindow
app=QApplication([])
try:
    w=MainWindow()
    # 选择 COM7 和 9600，连接真实硬件
    idx=w.port_combo.findText('COM7')
    if idx>=0: w.port_combo.setCurrentIndex(idx)
    w.baud_combo.setCurrentText('9600')
    w._connect()
    QTest.qWait(1500)
    print('connected=',w.connected,'rx=',w.rx_bytes,'mode=',w.mode_name,'battery=',w.lbl_batt.text())
    w._disconnect()
    w.close()
except Exception:
    traceback.print_exc()
