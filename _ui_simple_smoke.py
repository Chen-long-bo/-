import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path('PC_上位机').resolve()))
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
app=QApplication([])
try:
    w=MainWindow()
    print('before', w.spin_pid_mm.value(), w.pid_curve_panel.index)
    w.tabs.setCurrentIndex(w.pid_tab_index)
    print('after tab', w.spin_pid_mm.value(), w.pid_curve_panel.index)
    w.spin_pid_mm.setValue(300)
    print('set ok', w.spin_pid_mm.value())
    w._on_pid_start()
    print('pid start ok', w.pid_active)
    w._on_pid_abort()
    w.close()
except Exception:
    traceback.print_exc()
