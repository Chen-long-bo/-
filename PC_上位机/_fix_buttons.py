# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\ui\main_window.py"
lines = open(p, encoding="utf-8").read().split("\n")
out = []
for ln in lines:
    out.append(ln)
    if "layout.addWidget(self.btn_estop)" in ln:
        out += [
            "        self.btn_refresh.clicked.connect(self._refresh_ports)          # 刷新串口",
            "        self.btn_connect.clicked.connect(self._toggle_connection)      # 连接/断开",
            "        self.btn_estop.clicked.connect(lambda: self._send(protocol.cmd_stop_all()))   # 急停",
        ]
open(p, "w", encoding="utf-8").write("\n".join(out))
print("buttons connected")
