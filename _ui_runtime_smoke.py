import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path('PC_上位机').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from ui.main_window import MainWindow
app=QApplication([])
try:
    w=MainWindow()
    print('window ok', w.tabs.count(), 'params', w.param_table.rowCount())
    w.chk_demo.setChecked(True)
    w._connect()
    QTest.qWait(300)
    print('connected', w.connected, 'mode', w.mode_name, 'rx', w.rx_bytes)
    w._manual_button_pressed(1.0, 0.0)
    QTest.qWait(150)
    w._manual_button_released()
    w.tabs.setCurrentIndex(w.pid_tab_index)
    QTest.qWait(100)
    w._on_pid_start()
    QTest.qWait(300)
    print('pid', w.pid_active, w.lbl_pid_actual.text(), w.lbl_pid_error.text())
    w._on_pid_abort()
    w._disconnect()
    print('disconnect ok')
    w.close()
except Exception:
    traceback.print_exc()
