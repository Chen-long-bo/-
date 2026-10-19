# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\ui\main_window.py"
c = open(p, encoding="utf-8").read()

# _on_status 保存最近状态并更新调试中心计数
old = '    def _on_status(self, data):\n        """状态帧回调。"""\n        names = {0: "空闲", 1: "手动", 2: "缓停", 3: "PID停", 4: "路线", 5: "旋转"}   # 模式名'
new = '    def _on_status(self, data):\n        """状态帧回调。"""\n        self.last_status = data                           # 保存最近状态\n        if hasattr(self, "lbl_dbg_enc"):                  # 调试中心存在\n            self.lbl_dbg_enc.setText("计数: " + " / ".join(str(v) for v in data["enc"]))   # 更新计数\n        names = {0: "空闲", 1: "手动", 2: "缓停", 3: "PID停", 4: "路线", 5: "旋转"}   # 模式名'
assert old in c
c = c.replace(old, new, 1)

# _on_rx_activity 更新调试中心 RX/链路
old = '        self.lbl_rx.setText(f"{self.rx_bytes} bytes")     # 显示\n        if self.connected:                                # 已连接'
new = '        self.lbl_rx.setText(f"{self.rx_bytes} bytes")     # 显示\n        if hasattr(self, "lbl_dbg_rx"):                  # 调试中心存在\n            self.lbl_dbg_rx.setText(f"RX: {self.rx_bytes} bytes")   # 更新\n        if hasattr(self, "lbl_dbg_link"):                # 调试中心存在\n            self.lbl_dbg_link.setText("● 已连接（数据正常）")   # 更新\n        if self.connected:                                # 已连接'
assert old in c
c = c.replace(old, new, 1)

# _on_connection_changed 更新调试中心
old = '            self.lbl_conn.setText(f"● {msg}")             # 显示\n            self.lbl_conn.setStyleSheet("color:#00D1B2;") # 绿色'
new = '            self.lbl_conn.setText(f"● {msg}")             # 显示\n            self.lbl_conn.setStyleSheet("color:#00D1B2;") # 绿色\n            if hasattr(self, "lbl_dbg_link"):              # 调试中心存在\n                self.lbl_dbg_link.setText(f"● {msg}")      # 更新'
assert old in c
c = c.replace(old, new, 1)
old2 = '            self.lbl_conn.setText(f"● {msg}")             # 显示\n            self.lbl_conn.setStyleSheet("color:#FF5C6C;") # 红色'
new2 = '            self.lbl_conn.setText(f"● {msg}")             # 显示\n            self.lbl_conn.setStyleSheet("color:#FF5C6C;") # 红色\n            if hasattr(self, "lbl_dbg_link"):              # 调试中心存在\n                self.lbl_dbg_link.setText(f"● {msg}")      # 更新'
assert old2 in c
c = c.replace(old2, new2, 1)

# _update_link_status 更新调试中心
old = '            self.lbl_conn.setText("● 已连接（无数据）")     # 黄色提示\n            self.lbl_conn.setStyleSheet("color:#FFC857;") # 黄色'
new = '            self.lbl_conn.setText("● 已连接（无数据）")     # 黄色提示\n            self.lbl_conn.setStyleSheet("color:#FFC857;") # 黄色\n            if hasattr(self, "lbl_dbg_link"):              # 调试中心存在\n                self.lbl_dbg_link.setText("● 已连接（无数据）")   # 更新'
assert old in c
c = c.replace(old, new, 1)

open(p, "w", encoding="utf-8").write(c)
print("handlers patched")
