# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\ui\main_window.py"
c = open(p, encoding="utf-8").read()

# 1) 导入 time / math
if "import math" not in c:
    c = c.replace("import datetime                                 # 时间戳",
                  "import datetime                                 # 时间戳\nimport time                                     # 时间\nimport math                                     # 数学")

# 2) __init__ 增加 manual_pause_until
if "self.manual_pause_until" not in c:
    c = c.replace("        self.mode_name = \"空闲\"                          # 当前模式",
                  "        self.mode_name = \"空闲\"                          # 当前模式\n"
                  "        self.manual_pause_until = 0.0                    # 手动发送暂停截止时间")

# 3) 替换旋转/刹车按钮块
start = c.find("        rot = QGroupBox(\"原地旋转 / 刹车\")")
end = c.find("        return page                                       # 返回", start)
assert start != -1 and end != -1
new_block = '''        rot = QGroupBox("原地旋转 / 刹车")                  # 旋转刹车组
        rg = QGridLayout(rot)                             # 网格
        self.btn_rot_l45 = QPushButton("⟲ 左转45°")         # 左转45度
        self.btn_rot_l90 = QPushButton("⟲ 左转90°")         # 左转90度
        self.btn_rot_r45 = QPushButton("⟳ 右转45°")         # 右转45度
        self.btn_rot_r90 = QPushButton("⟳ 右转90°")         # 右转90度
        self.btn_brake_fast = QPushButton("急刹停")          # 急刹
        self.btn_brake_soft = QPushButton("缓停")            # 缓停
        self.btn_stop_all = QPushButton("全停")              # 全停
        rg.addWidget(self.btn_rot_l45, 0, 0)               # 加入
        rg.addWidget(self.btn_rot_l90, 0, 1)               # 加入
        rg.addWidget(self.btn_rot_r45, 1, 0)               # 加入
        rg.addWidget(self.btn_rot_r90, 1, 1)               # 加入
        rg.addWidget(self.btn_brake_fast, 2, 0)            # 加入
        rg.addWidget(self.btn_brake_soft, 2, 1)            # 加入
        rg.addWidget(self.btn_stop_all, 3, 0, 1, 2)        # 加入
        right.addWidget(rot)                               # 加入

        pos = QGroupBox("PID精准停")                        # 位置停组
        pl = QHBoxLayout(pos)                              # 水平
        self.spin_pid_mm = QSpinBox()                      # 距离输入
        self.spin_pid_mm.setRange(-5000, 5000)             # 范围
        self.spin_pid_mm.setValue(300)                     # 默认300mm
        self.spin_pid_mm.setSuffix(" mm")                  # 单位
        self.btn_pid_stop = QPushButton("开始精准停")       # 按钮
        pl.addWidget(self.spin_pid_mm)                     # 加入
        pl.addWidget(self.btn_pid_stop)                    # 加入
        right.addWidget(pos)                               # 加入
        right.addStretch(1)                                # 弹簧
        layout.addLayout(right, 1)                         # 加入
        self.btn_rot_l45.clicked.connect(lambda: self._rotate_angle(45))    # 左45
        self.btn_rot_l90.clicked.connect(lambda: self._rotate_angle(90))    # 左90
        self.btn_rot_r45.clicked.connect(lambda: self._rotate_angle(-45))   # 右45
        self.btn_rot_r90.clicked.connect(lambda: self._rotate_angle(-90))   # 右90
        self.btn_brake_fast.clicked.connect(lambda: self._special_send(protocol.cmd_brake_fast(), 0.6))   # 急刹
        self.btn_brake_soft.clicked.connect(lambda: self._special_send(protocol.cmd_brake_soft(), 0.6))   # 缓停
        self.btn_stop_all.clicked.connect(lambda: self._special_send(protocol.cmd_stop_all(), 0.6))       # 全停
        self.btn_pid_stop.clicked.connect(self._on_pid_stop)   # 精准停
'''
c = c[:start] + new_block + c[end:]

# 4) 模式名加“旋转”
c = c.replace('names = {0: "空闲", 1: "手动", 2: "缓停", 3: "PID停", 4: "路线"}   # 模式名',
              'names = {0: "空闲", 1: "手动", 2: "缓停", 3: "PID停", 4: "路线", 5: "旋转"}   # 模式名')

# 5) 手动 tick 增加暂停判断与摇杆灵敏度曲线
c = c.replace('        if self.tabs.currentIndex() != 0:                 # 不在手动Tab\n            return\n',
              '        if self.tabs.currentIndex() != 0:                 # 不在手动Tab\n            return\n'
              '        if time.time() < self.manual_pause_until:        # 特殊指令后短暂暂停\n            return\n')
c = c.replace('        vx = self.joy_y * (self.sl_vx.value() / 100.0)    # 摇杆前后\n        vy = -self.joy_x * (self.sl_vy.value() / 100.0)   # 摇杆左右',
              '        jy = math.copysign(abs(self.joy_y) ** 0.7, self.joy_y) if self.joy_y else 0.0   # 灵敏度曲线\n'
              '        jx = math.copysign(abs(self.joy_x) ** 0.7, self.joy_x) if self.joy_x else 0.0   # 灵敏度曲线\n'
              '        vx = jy * (self.sl_vx.value() / 100.0)          # 摇杆前后\n'
              '        vy = -jx * (self.sl_vy.value() / 100.0)         # 摇杆左右')

# 6) 增加 _rotate_angle / _special_send 方法
anchor = "    def _on_pid_stop(self):"
methods = '''    def _rotate_angle(self, deg):
        """原地旋转指定角度（正=左转，负=右转）。"""
        self.manual_pause_until = time.time() + 2.0       # 暂停手动发送，避免打断旋转
        self._send(protocol.cmd_rotate(deg))              # 发送旋转指令
        self._log(f"原地旋转 {deg}°")                      # 日志

    def _special_send(self, frame, pause_s=0.5):
        """发送刹车/停止等特殊指令，并短暂暂停手动发送。"""
        self.manual_pause_until = time.time() + pause_s   # 暂停手动发送
        self._send(frame)                                 # 发送

'''
if "_rotate_angle" not in c:
    c = c.replace(anchor, methods + anchor, 1)

open(p, "w", encoding="utf-8").write(c)
print("UI patched")
