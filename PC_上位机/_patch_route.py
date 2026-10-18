# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\ui\main_window.py"
c = open(p, encoding="utf-8").read()

# __init__ 增加 route_active
if "self.route_active" not in c:
    c = c.replace("        self.manual_pause_until = 0.0                    # 手动发送暂停截止时间",
                  "        self.manual_pause_until = 0.0                    # 手动发送暂停截止时间\n"
                  "        self.route_active = False                         # 固定路线是否运行中\n"
                  "        self.route_step = 0                               # 当前边序号0-3")

# 替换 _build_route_tab 方法
start = c.find("    def _build_route_tab(self):")
end = c.find("    def _build_pid_tab(self):", start)
assert start != -1 and end != -1
new_method = '''    def _build_route_tab(self):
        """固定路线Tab：由上位机按“前进-左转90°”循环4次组成正方形。"""
        page = QWidget()                                  # 页面
        layout = QVBoxLayout(page)                        # 垂直
        layout.setContentsMargins(18, 18, 18, 18)         # 边距
        box = QGroupBox("正方形路线（1×1米内）")            # 分组
        gl = QGridLayout(box)                             # 网格
        gl.addWidget(QLabel("边长"), 0, 0)                 # 标签
        self.spin_route = QSpinBox()                      # 边长
        self.spin_route.setRange(100, 1000)               # 范围
        self.spin_route.setValue(config.DEFAULT_ROUTE_SIDE_MM)   # 默认
        self.spin_route.setSuffix(" mm")                  # 单位
        gl.addWidget(self.spin_route, 0, 1)               # 加入
        gl.addWidget(QLabel("速度"), 0, 2)                 # 标签
        self.spin_route_speed = QDoubleSpinBox()          # 前进速度
        self.spin_route_speed.setRange(0.30, 1.00)        # 范围（>=0.3避免震动）
        self.spin_route_speed.setDecimals(2)              # 小数
        self.spin_route_speed.setSingleStep(0.05)         # 步进
        self.spin_route_speed.setValue(0.40)              # 默认
        gl.addWidget(self.spin_route_speed, 0, 3)         # 加入
        self.btn_route_start = QPushButton("开始")         # 开始
        self.btn_route_start.setObjectName("accent")      # 强调
        self.btn_route_stop = QPushButton("停止")          # 停止
        gl.addWidget(self.btn_route_start, 1, 0)          # 加入
        gl.addWidget(self.btn_route_stop, 1, 1)           # 加入
        self.lbl_route_progress = QLabel("未开始")         # 进度
        self.lbl_route_progress.setObjectName("value")    # 样式
        gl.addWidget(self.lbl_route_progress, 1, 2, 1, 2) # 加入
        note = QLabel("路线由上位机执行：前进边长 -> 左转90° -> 重复4次。")   # 说明
        note.setObjectName("sub")                         # 样式
        gl.addWidget(note, 2, 0, 1, 4)                    # 加入
        layout.addWidget(box)                             # 加入
        layout.addStretch(1)                              # 弹簧
        self.btn_route_start.clicked.connect(self._route_start)   # 开始
        self.btn_route_stop.clicked.connect(self._route_stop)     # 停止
        return page                                       # 返回

'''
c = c[:start] + new_method + c[end:]

# 插入路线状态机方法
anchor = "    def _build_pid_tab(self):"
methods = '''    def _route_start(self):
        """启动正方形路线。"""
        if not (self.worker and self.connected):          # 未连接
            self._log("请先连接小车")                      # 提示
            return
        self.route_active = True                          # 标记运行
        self.route_step = 0                               # 从第0边开始
        self.manual_pause_until = time.time() + 3600.0    # 暂停手动发送
        self.lbl_route_progress.setText("准备前进...")      # 提示
        self._route_forward()                             # 开始第一边

    def _route_forward(self):
        """路线：前进一条边。"""
        if not self.route_active:                         # 已停止
            return
        speed = self.spin_route_speed.value()             # 前进速度
        side_m = self.spin_route.value() / 1000.0         # 边长 m
        ms = max(300, int(side_m / speed * 1000))         # 前进时间
        self._send(protocol.cmd_manual(speed, 0.0, 0.0))  # 发送前进
        self.lbl_route_progress.setText(f"第 {self.route_step+1}/4 边：前进 {side_m:.2f} m")
        QTimer.singleShot(ms, self._route_turn)           # 时间到后转向

    def _route_turn(self):
        """路线：左转90°。"""
        if not self.route_active:                         # 已停止
            return
        self._send(protocol.cmd_rotate(90))               # 发送左转90°
        self.lbl_route_progress.setText(f"第 {self.route_step+1}/4 边：左转90°")
        QTimer.singleShot(1200, self._route_next)         # 等待转向完成

    def _route_next(self):
        """路线：进入下一条边。"""
        if not self.route_active:                         # 已停止
            return
        self.route_step += 1                              # 边序号加1
        if self.route_step >= 4:                          # 四条边完成
            self._route_finish()                          # 结束
        else:
            self._route_forward()                         # 下一条边

    def _route_finish(self):
        """路线完成。"""
        self.route_active = False                         # 清除运行
        self._send(protocol.cmd_stop_all())               # 停车
        self.manual_pause_until = 0.0                     # 恢复手动
        self.lbl_route_progress.setText("完成")            # 提示
        self._log("正方形路线完成")                        # 日志

    def _route_stop(self):
        """停止路线。"""
        self.route_active = False                         # 清除运行
        self._send(protocol.cmd_stop_all())               # 停车
        self.manual_pause_until = 0.0                     # 恢复手动
        self.lbl_route_progress.setText("已停止")          # 提示
        self._log("路线已停止")                            # 日志

'''
if "_route_start" not in c:
    c = c.replace(anchor, methods + anchor, 1)

# _manual_tick 中路线运行时禁止手动发送
c = c.replace('        if time.time() < self.manual_pause_until:        # 特殊指令后短暂暂停\n            return\n',
              '        if self.route_active:                            # 路线运行中\n            return\n'
              '        if time.time() < self.manual_pause_until:        # 特殊指令后短暂暂停\n            return\n')

open(p, "w", encoding="utf-8").write(c)
print("route UI patched")
