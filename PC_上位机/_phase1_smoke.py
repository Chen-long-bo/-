import os
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
app=QApplication([])
w=MainWindow(); w.show()
print("tabs:", w.tabs.count(), "| names:", [w.tabs.tabText(i) for i in range(w.tabs.count())])
# 几何预览
w.spin_geo_vx.setValue(0.3); w.spin_geo_vy.setValue(0.0); w.spin_geo_wz.setValue(0.0)
w._geo_compute(); print("geo:", w.lbl_geo.text())
# 编码器 CPR 标定（模拟状态）
w._on_status({"mode":1,"battery":12300,"enc":[0,0,0,0],"speed":[0,0,0,0]})
w._calib_record_start()
w._on_status({"mode":1,"battery":12300,"enc":[1000,1000,1000,1000],"speed":[0,0,0,0]})
w.spin_calib_mm.setValue(1000)
w._calib_compute_cpr(); print("cpr:", w.lbl_calib_result.text())
# 旋转标定
w.spin_calib_deg.setValue(45)
w._rotate_calib_compute(); print("rot:", w.lbl_rot_result.text())
print("debug link:", w.lbl_dbg_link.text(), "| rx:", w.lbl_dbg_rx.text())
app.quit()
print("UI DEBUG OK")
