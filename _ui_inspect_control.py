import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path('PC_上位机').resolve()))
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
app=QApplication([])
w=MainWindow()
s=w.tabs.widget(w.pid_tab_index)
print('scroll',s, 'widget', s.widget() if s else None)
for attr in ['spin_pid_mm','btn_pid_start','pid_curve_panel','lbl_pid_actual']:
    try:
        obj=getattr(w,attr)
        print(attr, obj, 'visible', obj.isVisible())
    except Exception as e:
        print(attr,'ERR',type(e).__name__,e)
