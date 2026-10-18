# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\ui\main_window.py"
c = open(p, encoding="utf-8").read()

# 在 PID 页的 layout.addWidget(box) 之后插入平滑组
anchor = "        layout.addWidget(box)                             # 加入\n        layout.addStretch(1)                              # 弹簧\n        self.btn_pid_apply.clicked.connect(self._on_pid_apply)"
if "chk_smooth" not in c:
    smooth = '''        layout.addWidget(box)                             # 加入
        smooth = QGroupBox("速度平滑（加速度限制）")        # 平滑组
        sg = QGridLayout(smooth)                          # 网格
        self.chk_smooth = QCheckBox("启用平滑（取消则急起急停）")   # 开关
        self.chk_smooth.setChecked(True)                  # 默认启用
        sg.addWidget(self.chk_smooth, 0, 0, 1, 2)         # 加入
        sg.addWidget(QLabel("线加速度 m/s²"), 1, 0)        # 标签
        self.spin_accel_v = QDoubleSpinBox()              # 线加速度
        self.spin_accel_v.setRange(0.1, 5.0)              # 范围
        self.spin_accel_v.setDecimals(2)                  # 小数
        self.spin_accel_v.setSingleStep(0.1)              # 步进
        self.spin_accel_v.setValue(1.0)                   # 默认
        sg.addWidget(self.spin_accel_v, 1, 1)             # 加入
        sg.addWidget(QLabel("角加速度 rad/s²"), 2, 0)      # 标签
        self.spin_accel_w = QDoubleSpinBox()              # 角加速度
        self.spin_accel_w.setRange(0.5, 10.0)             # 范围
        self.spin_accel_w.setDecimals(2)                  # 小数
        self.spin_accel_w.setSingleStep(0.5)              # 步进
        self.spin_accel_w.setValue(3.0)                   # 默认
        sg.addWidget(self.spin_accel_w, 2, 1)             # 加入
        self.btn_accel_apply = QPushButton("下发平滑参数")  # 按钮
        self.btn_accel_apply.setObjectName("accent")      # 强调
        sg.addWidget(self.btn_accel_apply, 3, 0, 1, 2)    # 加入
        layout.addWidget(smooth)                          # 加入
        layout.addStretch(1)                              # 弹簧
        self.btn_pid_apply.clicked.connect(self._on_pid_apply)'''
    c = c.replace(anchor, smooth, 1)
    c = c.replace('        self.btn_pid_read.clicked.connect(lambda: self._send(protocol.cmd_read_params()))   # 读取',
                  '        self.btn_pid_read.clicked.connect(lambda: self._send(protocol.cmd_read_params()))   # 读取\n'
                  '        self.btn_accel_apply.clicked.connect(self._on_accel_apply)   # 下发平滑参数')

# 增加 _on_accel_apply 方法
anchor2 = "    def _on_pid_apply(self):"
method = '''    def _on_accel_apply(self):
        """下发加速度限制（速度平滑）。"""
        if self.chk_smooth.isChecked():                   # 启用平滑
            self._send(protocol.cmd_set_accel(self.spin_accel_v.value(),
                                              self.spin_accel_w.value()))
            self._log("已下发平滑参数")
        else:                                             # 关闭平滑
            self._send(protocol.cmd_set_accel(1000.0, 1000.0))
            self._log("已关闭平滑（急起急停）")

'''
if "def _on_accel_apply" not in c:
    c = c.replace(anchor2, method + anchor2, 1)

open(p, "w", encoding="utf-8").write(c)
print("smooth UI patched")
