# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\ui\main_window.py"
c = open(p, encoding="utf-8").read()

# __init__ 增加链路诊断状态与定时器
if "self.last_rx_time" not in c:
    c = c.replace("        self.route_gen = 0                                # 路线运行代号，用于作废旧定时器",
                  "        self.route_gen = 0                                # 路线运行代号，用于作废旧定时器\n"
                  "        self.last_rx_time = 0.0                           # 最近收到数据的时间\n"
                  "        self.rx_bytes = 0                                 # 累计接收字节数\n"
                  "        self.link_test_pending = False                    # 是否在等待链路测试ACK")
    c = c.replace("        self.timer.start(config.TX_INTERVAL_MS)          # 启动",
                  "        self.timer.start(config.TX_INTERVAL_MS)          # 启动\n"
                  "        self.link_timer = QTimer(self)                    # 链路状态定时器\n"
                  "        self.link_timer.timeout.connect(self._update_link_status)   # 更新链路状态\n"
                  "        self.link_timer.start(1000)                       # 每秒更新")

# 连接区增加“测试链路”按钮
c = c.replace("        h.addWidget(self.btn_refresh)                     # 加入\n        h.addWidget(self.btn_connect)                     # 加入",
              "        h.addWidget(self.btn_refresh)                     # 加入\n"
              "        h.addWidget(self.btn_connect)                     # 加入\n"
              "        self.btn_link_test = QPushButton(\"测试链路\")      # 链路测试\n"
              "        h.addWidget(self.btn_link_test)                   # 加入")
c = c.replace("        self.btn_connect.clicked.connect(self._toggle_connection)      # 连接/断开",
              "        self.btn_connect.clicked.connect(self._toggle_connection)      # 连接/断开\n"
              "        self.btn_link_test.clicked.connect(self._link_test)            # 测试链路")

# 状态区增加接收字节
c = c.replace("        sl.addWidget(QLabel(\"编码器\"), 3, 0)               # 编码器标签\n        self.lbl_enc = QLabel(\"0 / 0 / 0 / 0\")           # 编码器值\n        sl.addWidget(self.lbl_enc, 3, 1)                  # 加入",
              "        sl.addWidget(QLabel(\"编码器\"), 3, 0)               # 编码器标签\n"
              "        self.lbl_enc = QLabel(\"0 / 0 / 0 / 0\")           # 编码器值\n"
              "        sl.addWidget(self.lbl_enc, 3, 1)                  # 加入\n"
              "        sl.addWidget(QLabel(\"接收\"), 4, 0)                # 接收标签\n"
              "        self.lbl_rx = QLabel(\"0 bytes\")                   # 接收字节\n"
              "        sl.addWidget(self.lbl_rx, 4, 1)                   # 加入")

# 模式初值改为 --
c = c.replace('        self.lbl_mode = QLabel("空闲")                    # 模式值', '        self.lbl_mode = QLabel("--")                      # 模式值（未收到数据）')

# 连接信号：rx_activity
c = c.replace('        self.worker.rx_log.connect(lambda x: None)                            # 接收日志暂不显示',
              '        self.worker.rx_log.connect(lambda x: None)                            # 接收日志暂不显示\n'
              '        self.worker.rx_activity.connect(self._on_rx_activity)                 # 接收活动')

# 断开时恢复模式显示
c = c.replace('        self.statusBar().showMessage("未连接")             # 状态栏',
              '        self.lbl_mode.setText("--")                        # 模式显示为空\n'
              '        self.statusBar().showMessage("未连接")             # 状态栏')

# 连接成功时初始化接收统计
c = c.replace('            self._send(protocol.cmd_heartbeat())          # 发心跳',
              '            self.last_rx_time = time.time()               # 重置接收时间\n'
              '            self.rx_bytes = 0                             # 重置字节数\n'
              '            self.lbl_rx.setText("0 bytes")                # 显示\n'
              '            self._send(protocol.cmd_heartbeat())          # 发心跳')

# ACK 处理链路测试
c = c.replace('    def _on_ack(self, data):\n        """ACK回调。"""\n        self._log(f"ACK cmd=0x{data[\'cmd\']:02X} err={data[\'err\']}")   # 日志',
              '    def _on_ack(self, data):\n'
              '        """ACK回调。"""\n'
              '        self._log(f"ACK cmd=0x{data[\'cmd\']:02X} err={data[\'err\']}")   # 日志\n'
              '        if self.link_test_pending and data["cmd"] == config.CMD_HEARTBEAT:   # 链路测试\n'
              '            self.link_test_pending = False            # 清除等待\n'
              '            self._log("链路测试成功：收到心跳ACK")     # 提示')

# 增加链路诊断方法
anchor = "    def _on_joystick(self, x, y):"
methods = '''    def _on_rx_activity(self, n):
        """收到串口数据时更新统计。"""
        self.last_rx_time = time.time()                   # 记录时间
        self.rx_bytes += n                                # 累加字节
        self.lbl_rx.setText(f"{self.rx_bytes} bytes")     # 显示
        if self.connected:                                # 已连接
            self.lbl_conn.setText("● 已连接（数据正常）")   # 绿色提示
            self.lbl_conn.setStyleSheet("color:#00D1B2;") # 绿色

    def _update_link_status(self):
        """每秒检查一次是否有数据。"""
        if not self.connected:                            # 未连接
            return
        if time.time() - self.last_rx_time > 1.5:         # 超过1.5秒没数据
            self.lbl_conn.setText("● 已连接（无数据）")     # 黄色提示
            self.lbl_conn.setStyleSheet("color:#FFC857;") # 黄色
        else:
            self.lbl_conn.setText("● 已连接（数据正常）")   # 绿色提示
            self.lbl_conn.setStyleSheet("color:#00D1B2;") # 绿色

    def _link_test(self):
        """发送心跳并等待ACK，判断链路是否正常。"""
        if not (self.worker and self.connected):          # 未连接
            self._log("请先连接")                          # 提示
            return
        self.link_test_pending = True                     # 标记等待
        self._send(protocol.cmd_heartbeat())              # 发心跳
        self._log("已发送心跳，等待 ACK...")               # 提示
        QTimer.singleShot(1500, self._link_test_timeout)  # 超时检查

    def _link_test_timeout(self):
        """链路测试超时。"""
        if self.link_test_pending:                        # 仍在等待
            self.link_test_pending = False                # 清除
            self._log("链路测试失败：1.5秒内未收到ACK（检查接线/波特率/AT模式）")

'''
if "def _on_rx_activity" not in c:
    c = c.replace(anchor, methods + anchor, 1)

open(p, "w", encoding="utf-8").write(c)
print("link diagnostics patched")
