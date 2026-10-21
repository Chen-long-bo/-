import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path('PC_上位机').resolve()))
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
app = QApplication([])
try:
    w = MainWindow()
    print('window ok', w.tabs.count())
    print('ports', [w.port_combo.itemText(i) for i in range(w.port_combo.count())])
    print('tabs', [w.tabs.tabText(i) for i in range(w.tabs.count())])
    print('manual speed', w.sl_speed.value())
    print('parameter rows', w.param_table.rowCount())
    w.close()
except Exception:
    traceback.print_exc()
