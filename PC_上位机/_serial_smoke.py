import os
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from serial_worker import SerialWorker
import protocol
app=QApplication([])
w=SerialWorker("COM5",115200)
res={}
def on_conn(ok,msg): print("conn:",ok,msg)
def on_status(d): res["status"]=d
def on_curve(d): res["curve"]=d
w.connection_changed.connect(on_conn)
w.status_received.connect(on_status)
w.curve_received.connect(on_curve)
w.start()
def send_manual():
    w.send_frame(protocol.cmd_manual(0.35,0,0))
QTimer.singleShot(800, send_manual)
def finish():
    print("status:", res.get("status"))
    print("curve:", res.get("curve"))
    w.stop(); w.wait(1000)
    app.quit()
QTimer.singleShot(1800, finish)
app.exec()
print("SERIAL SMOKE OK")
