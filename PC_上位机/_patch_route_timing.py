# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\ui\main_window.py"
c = open(p, encoding="utf-8").read()

# __init__ 增加 route_gen
if "self.route_gen" not in c:
    c = c.replace("        self.route_step = 0                               # 当前边序号0-3",
                  "        self.route_step = 0                               # 当前边序号0-3\n"
                  "        self.route_gen = 0                                # 路线运行代号，用于作废旧定时器")

# 替换路线方法块
start = c.find("    def _route_start(self):")
end = c.find("    def _build_pid_tab(self):", start)
assert start != -1 and end != -1
new_block = '''    def _route_start(self):
        """启动正方形路线。"""
        if self.route_active:                             # 已在运行
            return
        if not (self.worker and self.connected):          # 未连接
            self._log("请先连接小车")                      # 提示
            return
        self.route_gen += 1                               # 生成新的运行代号
        self.route_active = True                          # 标记运行
        self.route_step = 0                               # 从第0边开始
        self.manual_pause_until = time.time() + 3600.0    # 暂停手动发送
        self.lbl_route_progress.setText("准备前进...")      # 提示
        self._route_forward(self.route_gen)               # 开始第一边

    def _route_forward(self, g):
        """路线：前进一条边。"""
        if g != self.route_gen or not self.route_active:  # 已停止/已作废
            return
        speed = self.spin_route_speed.value()             # 前进速度
        side_m = self.spin_route.value() / 1000.0         # 边长 m
        ms = max(300, int(side_m / speed * 1000))         # 前进时间
        self._send(protocol.cmd_manual(speed, 0.0, 0.0))  # 发送前进
        self.lbl_route_progress.setText(f"第 {self.route_step+1}/4 边：前进 {side_m:.2f} m")
        QTimer.singleShot(ms, lambda: self._route_pause_after_forward(g))   # 前进结束

    def _route_pause_after_forward(self, g):
        """前进后停顿。"""
        if g != self.route_gen or not self.route_active:  # 已停止
            return
        self._send(protocol.cmd_stop_all())               # 先停一下
        self.lbl_route_progress.setText(f"第 {self.route_step+1}/4 边：停顿")
        QTimer.singleShot(self.spin_route_pause.value(), lambda: self._route_turn(g))

    def _route_turn(self, g):
        """路线：左转90°。"""
        if g != self.route_gen or not self.route_active:  # 已停止
            return
        self._send(protocol.cmd_rotate(90))               # 发送左转90°
        self.lbl_route_progress.setText(f"第 {self.route_step+1}/4 边：左转90°")
        QTimer.singleShot(1200, lambda: self._route_pause_after_turn(g))   # 等待转向完成

    def _route_pause_after_turn(self, g):
        """转向后停顿。"""
        if g != self.route_gen or not self.route_active:  # 已停止
            return
        self.lbl_route_progress.setText(f"第 {self.route_step+1}/4 边：停顿")
        QTimer.singleShot(self.spin_route_pause.value(), lambda: self._route_next(g))

    def _route_next(self, g):
        """路线：进入下一条边。"""
        if g != self.route_gen or not self.route_active:  # 已停止
            return
        self.route_step += 1                              # 边序号加1
        if self.route_step >= 4:                          # 四条边完成
            self._route_finish()                          # 结束
        else:
            self._route_forward(g)                        # 下一条边

    def _route_finish(self):
        """路线完成。"""
        self.route_gen += 1                               # 作废所有待执行定时器
        self.route_active = False                         # 清除运行
        self._send(protocol.cmd_stop_all())               # 停车
        self.manual_pause_until = 0.0                     # 恢复手动
        self.lbl_route_progress.setText("完成")            # 提示
        self._log("正方形路线完成")                        # 日志

    def _route_stop(self):
        """停止路线。"""
        self.route_gen += 1                               # 作废所有待执行定时器
        self.route_active = False                         # 清除运行
        self._send(protocol.cmd_stop_all())               # 停车
        self.manual_pause_until = 0.0                     # 恢复手动
        self.lbl_route_progress.setText("已停止")          # 提示
        self._log("路线已停止")                            # 日志

'''
c = c[:start] + new_block + c[end:]

# 路线Tab增加停顿输入
old_note = '''        note = QLabel("路线由上位机执行：前进边长 -> 左转90° -> 重复4次。")   # 说明
        note.setObjectName("sub")                         # 样式
        gl.addWidget(note, 2, 0, 1, 4)                    # 加入'''
new_note = '''        gl.addWidget(QLabel("停顿"), 2, 0)                 # 标签
        self.spin_route_pause = QSpinBox()                # 停顿时间
        self.spin_route_pause.setRange(0, 3000)           # 范围
        self.spin_route_pause.setValue(500)               # 默认500ms
        self.spin_route_pause.setSuffix(" ms")            # 单位
        gl.addWidget(self.spin_route_pause, 2, 1)         # 加入
        note = QLabel("前进 -> 停顿 -> 左转90° -> 停顿 -> 重复4次。")   # 说明
        note.setObjectName("sub")                         # 样式
        gl.addWidget(note, 3, 0, 1, 4)                    # 加入'''
assert old_note in c
c = c.replace(old_note, new_note, 1)

open(p, "w", encoding="utf-8").write(c)
print("route timing patched")
