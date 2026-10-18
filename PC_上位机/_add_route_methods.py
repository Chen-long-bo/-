# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\ui\main_window.py"
c = open(p, encoding="utf-8").read()
if "def _route_start" not in c:
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
    assert anchor in c
    c = c.replace(anchor, methods + anchor, 1)
    open(p, "w", encoding="utf-8").write(c)
    print("route methods inserted")
else:
    print("already present")
