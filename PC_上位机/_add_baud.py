# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\ui\main_window.py"
lines = open(p, encoding="utf-8").read().split("\n")
out = []
for ln in lines:
    out.append(ln)
    if "cl.addWidget(self.port_combo)" in ln and "加入" in ln:
        out += [
            "        bh = QHBoxLayout()                                 # 波特率行",
            "        bh.addWidget(QLabel(\"波特率\"))                      # 标签",
            "        self.baud_combo = QComboBox()                      # 波特率下拉",
            "        for b in config.BAUDRATE_OPTIONS:                  # 加入选项",
            "            self.baud_combo.addItem(str(b))                # 添加",
            "        self.baud_combo.setCurrentText(str(config.SERIAL_BAUDRATE))   # 默认",
            "        bh.addWidget(self.baud_combo)                      # 加入",
            "        cl.addLayout(bh)                                   # 加入连接分组",
            "        self.port_combo.currentTextChanged.connect(self._on_port_changed)   # 端口变化自动匹配波特率",
        ]
    if "self.port_combo.setCurrentText(config.DEFAULT_PORT)" in ln:
        out.append("        self._on_port_changed(self.port_combo.currentText())   # 自动匹配波特率")
    if "self.worker = SerialWorker(port)" in ln:
        out[-1] = "            baud = int(self.baud_combo.currentText())     # 当前波特率"
        out.append("            self.worker = SerialWorker(port, baud)        # 创建串口线程")
# 插入 _on_port_changed 方法（放在 _refresh_ports 前）
text = "\n".join(out)
anchor = "    def _refresh_ports(self):"
method = ("    def _on_port_changed(self, port):\n"
          "        \"\"\"端口变化时自动匹配波特率。\"\"\"\n"
          "        if port in config.PORT_BAUDRATE:               # 有指定波特率\n"
          "            self.baud_combo.setCurrentText(str(config.PORT_BAUDRATE[port]))   # 设置\n\n")
text = text.replace(anchor, method + anchor, 1)
open(p, "w", encoding="utf-8").write(text)
print("patched")
