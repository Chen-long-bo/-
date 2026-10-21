import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path('PC_上位机').resolve()))
from PySide6.QtWidgets import QApplication, QScrollArea
from ui.main_window import MainWindow
app=QApplication([])
w=MainWindow()
for i in range(w.tabs.count()):
    try:
        wd=w.tabs.widget(i)
        print(i, w.tabs.tabText(i), type(wd).__name__ if wd else None, wd.isVisible() if wd else None)
    except Exception as e:
        print(i,'ERR',e)
try:
    print('pid scroll', type(w.tabs.widget(w.pid_tab_index)).__name__)
except Exception as e: print('pid err',e)
try:
    print('param table',w.param_table.rowCount())
except Exception as e: print('param err',e)
