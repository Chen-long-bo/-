import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path('PC_上位机').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from ui.main_window import MainWindow
app=QApplication([])
w=MainWindow()
print('ports', [w.port_combo.itemText(i) for i in range(w.port_combo.count())], 'current',w.port_combo.currentText(),'baud',w.baud_combo.currentText())
idx=w.port_combo.findText('COM7'); print('idx',idx)
w.port_combo.setCurrentIndex(idx)
w.baud_combo.setCurrentText('9600')
print('selected',w.port_combo.currentText(),w.baud_combo.currentText())
w._connect()
QTest.qWait(2000)
print('connected',w.connected,'worker',w.worker)
print('logs:',w.log_view.toPlainText())
if w.worker:
    w._disconnect()
w.close()
