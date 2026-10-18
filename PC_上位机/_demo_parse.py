import os
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PySide6.QtWidgets import QApplication
import protocol
from demo_worker import DemoWorker
app=QApplication([])
d=DemoWorker()
f=protocol.cmd_manual(0.3,0,0)
print("frame", f.hex(" "))
d.send_frame(f)
print("mode", d.mode, "target", d.target)
d._update(0.05)
print("wheel", d.target_wheel, "actual", d.actual)
