# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\ui\main_window.py"
c = open(p, encoding="utf-8").read()

# 1) 导入 QScrollArea
c = c.replace("QLineEdit, QFrame, QSizePolicy, QMessageBox", "QLineEdit, QFrame, QSizePolicy, QMessageBox, QScrollArea")

# 2) 增加调试中心 Tab
old_tabs = '        self.tabs.addTab(self._build_curve_tab(), "数据曲线")      # 曲线\n        self.tabs.addTab(self._build_log_tab(), "日志")            # 日志'
new_tabs = '        self.tabs.addTab(self._build_curve_tab(), "数据曲线")      # 曲线\n        self.tabs.addTab(self._build_debug_tab(), "调试中心")      # 调试中心\n        self.tabs.addTab(self._build_log_tab(), "日志")            # 日志'
assert old_tabs in c
c = c.replace(old_tabs, new_tabs, 1)

# 3) 调试标定状态
c = c.replace('        self.link_test_pending = False                    # 是否在等待链路测试ACK',
              '        self.link_test_pending = False                    # 是否在等待链路测试ACK\n'
              '        self.last_status = None                           # 最近一次状态帧\n'
              '        self.calib_start_counts = None                    # 编码器标定起点计数')

# 4) 删除手动页 PID 分组
start = c.find('        pos = QGroupBox("PID精准停")')
end = c.find('        right.addStretch(1)', start)
assert start != -1 and end != -1
c = c[:start] + c[end:]
c = c.replace('        self.btn_pid_stop.clicked.connect(self._on_pid_stop)   # 精准停\n', '', 1)

# 5) 在 PID 页插入 PID 测试分组（放在平滑组之前）
old = '        layout.addWidget(box)                             # 加入\n        smooth = QGroupBox("速度平滑（加速度限制）")        # 平滑组'
new = '''        layout.addWidget(box)                             # 加入

        pidtest = QGroupBox("【算法】位置环 PID 测试")      # PID测试组
        pt = QHBoxLayout(pidtest)                          # 水平
        self.spin_pid_mm = QSpinBox()                      # 距离输入
        self.spin_pid_mm.setRange(-5000, 5000)             # 范围
        self.spin_pid_mm.setValue(300)                     # 默认300mm
        self.spin_pid_mm.setSuffix(" mm")                  # 单位
        self.btn_pid_stop = QPushButton("开始 PID 测试")    # 测试按钮
        self.btn_pid_stop.setObjectName("accent")          # 强调
        pt.addWidget(self.spin_pid_mm)                     # 加入
        pt.addWidget(self.btn_pid_stop)                    # 加入
        layout.addWidget(pidtest)                          # 加入
        note = QLabel("说明：这是位置环 PID 测试，不属于手动遥控。")   # 说明
        note.setObjectName("sub")                          # 样式
        layout.addWidget(note)                             # 加入
        self.btn_pid_stop.clicked.connect(self._on_pid_stop)   # 测试

        smooth = QGroupBox("速度平滑（加速度限制）")        # 平滑组'''
assert old in c
c = c.replace(old, new, 1)

open(p, "w", encoding="utf-8").write(c)
print("step1 patched")
