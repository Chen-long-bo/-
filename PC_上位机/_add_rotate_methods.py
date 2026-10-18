# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\ui\main_window.py"
c = open(p, encoding="utf-8").read()
if "def _rotate_angle" not in c:
    anchor = "    def _on_pid_stop(self):"
    methods = (
        "    def _rotate_angle(self, deg):\n"
        "        \"\"\"原地旋转指定角度（正=左转，负=右转）。\"\"\"\n"
        "        self.manual_pause_until = time.time() + 2.0       # 暂停手动发送，避免打断旋转\n"
        "        self._send(protocol.cmd_rotate(deg))              # 发送旋转指令\n"
        "        self._log(f\"原地旋转 {deg}°\")                      # 日志\n\n"
        "    def _special_send(self, frame, pause_s=0.5):\n"
        "        \"\"\"发送刹车/停止等特殊指令，并短暂暂停手动发送。\"\"\"\n"
        "        self.manual_pause_until = time.time() + pause_s   # 暂停手动发送\n"
        "        self._send(frame)                                 # 发送\n\n"
    )
    assert anchor in c

    c = c.replace(anchor, methods + anchor, 1)
    open(p, "w", encoding="utf-8").write(c)
    print("methods inserted")
else:
    print("already present")
