# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\ui\main_window.py"
c = open(p, encoding="utf-8").read()

anchor = "    def _build_log_tab(self):"
method = '''    def _build_debug_tab(self):
        """调试中心：链路、标定、点动、算法预览。"""
        scroll = QScrollArea()                             # 滚动区
        scroll.setWidgetResizable(True)                    # 自适应
        page = QWidget()                                   # 页面
        layout = QVBoxLayout(page)                         # 垂直布局
        layout.setContentsMargins(16, 16, 16, 16)          # 边距
        layout.setSpacing(12)                              # 间距

        link = QGroupBox("【调试】链路状态")                # 链路组
        ll = QVBoxLayout(link)                             # 布局
        self.lbl_dbg_link = QLabel("未连接")               # 状态
        self.lbl_dbg_rx = QLabel("RX: 0 bytes")           # 接收字节
        ll.addWidget(self.lbl_dbg_link)                    # 加入
        ll.addWidget(self.lbl_dbg_rx)                      # 加入
        lh = QHBoxLayout()                                 # 按钮行
        b_test = QPushButton("测试链路")                   # 测试
        b_test.clicked.connect(self._link_test)            # 连接
        b_heart = QPushButton("发送心跳")                  # 心跳
        b_heart.clicked.connect(lambda: self._send(protocol.cmd_heartbeat()))   # 连接
        lh.addWidget(b_test)                               # 加入
        lh.addWidget(b_heart)                              # 加入
        ll.addLayout(lh)                                   # 加入
        layout.addWidget(link)                             # 加入页面

        raw = QGroupBox("【调试】原始帧发送")              # 原始帧组
        rl = QHBoxLayout(raw)                              # 水平
        self.edit_raw = QLineEdit()                        # 输入框
        self.edit_raw.setPlaceholderText("AA 55 01 0A 0B") # 提示
        b_raw = QPushButton("发送十六进制")                # 发送
        b_raw.clicked.connect(self._send_raw_frame)        # 连接
        rl.addWidget(self.edit_raw)                        # 加入
        rl.addWidget(b_raw)                                # 加入
        layout.addWidget(raw)                              # 加入页面

        cal = QGroupBox("【标定】编码器 CPR")               # 编码器标定
        cl = QGridLayout(cal)                              # 网格
        self.lbl_dbg_cpr = QLabel(f"当前 CPR: {config.ENCODER_CPR:.0f}")   # CPR
        self.lbl_dbg_enc = QLabel("计数: --")              # 计数
        cl.addWidget(self.lbl_dbg_cpr, 0, 0, 1, 2)         # 加入
        cl.addWidget(self.lbl_dbg_enc, 1, 0, 1, 2)         # 加入
        cl.addWidget(QLabel("实际行驶距离"), 2, 0)          # 标签
        self.spin_calib_mm = QDoubleSpinBox()              # 距离
        self.spin_calib_mm.setRange(10, 5000)              # 范围
        self.spin_calib_mm.setDecimals(1)                  # 小数
        self.spin_calib_mm.setValue(1000)                  # 默认
        self.spin_calib_mm.setSuffix(" mm")                # 单位
        cl.addWidget(self.spin_calib_mm, 2, 1)             # 加入
        b_start = QPushButton("记录起点")                  # 起点
        b_start.clicked.connect(self._calib_record_start)  # 连接
        b_calc = QPushButton("记录终点并计算")             # 计算
        b_calc.clicked.connect(self._calib_compute_cpr)    # 连接
        cl.addWidget(b_start, 3, 0)                        # 加入
        cl.addWidget(b_calc, 3, 1)                         # 加入
        self.lbl_calib_result = QLabel("建议 CPR: --")     # 结果
        self.lbl_calib_result.setObjectName("value")       # 样式
        cl.addWidget(self.lbl_calib_result, 4, 0, 1, 2)    # 加入
        layout.addWidget(cal)                              # 加入页面

        rot = QGroupBox("【标定】原地旋转时间")            # 旋转标定
        rl2 = QGridLayout(rot)                             # 网格
        self.lbl_rot_result = QLabel(f"当前 90° 时间: {config.ROTATE_MS_PER_90} ms")   # 当前
        rl2.addWidget(self.lbl_rot_result, 0, 0, 1, 2)     # 加入
        rl2.addWidget(QLabel("实测角度"), 1, 0)             # 标签
        self.spin_calib_deg = QDoubleSpinBox()             # 角度
        self.spin_calib_deg.setRange(1, 360)               # 范围
        self.spin_calib_deg.setDecimals(1)                 # 小数
        self.spin_calib_deg.setValue(90)                   # 默认
        self.spin_calib_deg.setSuffix(" °")                # 单位
        rl2.addWidget(self.spin_calib_deg, 1, 1)           # 加入
        b_90 = QPushButton("发送 90°")                     # 发送
        b_90.clicked.connect(self._rotate_calib_send)      # 连接
        b_calc2 = QPushButton("计算建议时间")              # 计算
        b_calc2.clicked.connect(self._rotate_calib_compute) # 连接
        rl2.addWidget(b_90, 2, 0)                          # 加入
        rl2.addWidget(b_calc2, 2, 1)                       # 加入
        layout.addWidget(rot)                              # 加入页面

        mot = QGroupBox("【调试】运动点动（短脉冲 600ms）")   # 运动点动
        ml = QGridLayout(mot)                              # 网格
        self.btn_dbg_forward = QPushButton("前进")         # 前进
        self.btn_dbg_back = QPushButton("后退")            # 后退
        self.btn_dbg_left = QPushButton("左移")            # 左移
        self.btn_dbg_right = QPushButton("右移")           # 右移
        self.btn_dbg_rot_l = QPushButton("左转")           # 左转
        self.btn_dbg_rot_r = QPushButton("右转")           # 右转
        self.btn_dbg_forward.clicked.connect(lambda: self._pulse_motion(0.3, 0.0, 0.0, 600))   # 前进
        self.btn_dbg_back.clicked.connect(lambda: self._pulse_motion(-0.3, 0.0, 0.0, 600))     # 后退
        self.btn_dbg_left.clicked.connect(lambda: self._pulse_motion(0.0, 0.3, 0.0, 600))      # 左移
        self.btn_dbg_right.clicked.connect(lambda: self._pulse_motion(0.0, -0.3, 0.0, 600))    # 右移
        self.btn_dbg_rot_l.clicked.connect(lambda: self._pulse_motion(0.0, 0.0, 0.6, 600))     # 左转
        self.btn_dbg_rot_r.clicked.connect(lambda: self._pulse_motion(0.0, 0.0, -0.6, 600))    # 右转
        ml.addWidget(self.btn_dbg_forward, 0, 0)           # 加入
        ml.addWidget(self.btn_dbg_back, 0, 1)              # 加入
        ml.addWidget(self.btn_dbg_left, 1, 0)              # 加入
        ml.addWidget(self.btn_dbg_right, 1, 1)             # 加入
        ml.addWidget(self.btn_dbg_rot_l, 2, 0)             # 加入
        ml.addWidget(self.btn_dbg_rot_r, 2, 1)             # 加入
        layout.addWidget(mot)                              # 加入页面

        geo = QGroupBox("【算法】麦轮逆运动学预览")        # 几何预览
        gl = QGridLayout(geo)                              # 网格
        gl.addWidget(QLabel("vx"), 0, 0)                   # 标签
        self.spin_geo_vx = QDoubleSpinBox()                # vx
        self.spin_geo_vx.setRange(-1.0, 1.0)               # 范围
        self.spin_geo_vx.setDecimals(2)                    # 小数
        self.spin_geo_vx.setValue(0.3)                     # 默认
        gl.addWidget(self.spin_geo_vx, 0, 1)               # 加入
        gl.addWidget(QLabel("vy"), 1, 0)                   # 标签
        self.spin_geo_vy = QDoubleSpinBox()                # vy
        self.spin_geo_vy.setRange(-1.0, 1.0)               # 范围
        self.spin_geo_vy.setDecimals(2)                    # 小数
        self.spin_geo_vy.setValue(0.0)                     # 默认
        gl.addWidget(self.spin_geo_vy, 1, 1)               # 加入
        gl.addWidget(QLabel("wz"), 2, 0)                   # 标签
        self.spin_geo_wz = QDoubleSpinBox()                # wz
        self.spin_geo_wz.setRange(-2.0, 2.0)               # 范围
        self.spin_geo_wz.setDecimals(2)                    # 小数
        self.spin_geo_wz.setValue(0.0)                     # 默认
        gl.addWidget(self.spin_geo_wz, 2, 1)               # 加入
        b_geo = QPushButton("计算四轮速度")                # 计算
        b_geo.clicked.connect(self._geo_compute)           # 连接
        gl.addWidget(b_geo, 3, 0, 1, 2)                    # 加入
        self.lbl_geo = QLabel("A/B/C/D: --")               # 结果
        self.lbl_geo.setObjectName("value")                # 样式
        self.lbl_geo.setWordWrap(True)                     # 换行
        gl.addWidget(self.lbl_geo, 4, 0, 1, 2)             # 加入
        layout.addWidget(geo)                              # 加入页面

        acc = QGroupBox("【算法】加速度平滑")              # 加速度组
        al = QGridLayout(acc)                              # 网格
        al.addWidget(QLabel("线加速度 m/s²"), 0, 0)        # 标签
        self.spin_dbg_accel_v = QDoubleSpinBox()           # 线加速度
        self.spin_dbg_accel_v.setRange(0.1, 5.0)           # 范围
        self.spin_dbg_accel_v.setDecimals(2)               # 小数
        self.spin_dbg_accel_v.setValue(config.ACCEL_V)     # 默认
        al.addWidget(self.spin_dbg_accel_v, 0, 1)          # 加入
        al.addWidget(QLabel("角加速度 rad/s²"), 1, 0)      # 标签
        self.spin_dbg_accel_w = QDoubleSpinBox()           # 角加速度
        self.spin_dbg_accel_w.setRange(0.5, 10.0)          # 范围
        self.spin_dbg_accel_w.setDecimals(2)               # 小数
        self.spin_dbg_accel_w.setValue(config.ACCEL_W)     # 默认
        al.addWidget(self.spin_dbg_accel_w, 1, 1)          # 加入
        b_acc = QPushButton("下发平滑参数")                # 下发
        b_acc.clicked.connect(self._debug_accel_apply)     # 连接
        al.addWidget(b_acc, 2, 0, 1, 2)                    # 加入
        layout.addWidget(acc)                              # 加入页面

        ov = QGroupBox("【参数】当前关键参数")              # 参数总览
        ol = QVBoxLayout(ov)                               # 布局
        text = (f"CPR: {config.ENCODER_CPR:.0f} counts/rev    "
                f"轮径: {config.WHEEL_DIAMETER_MM:.1f} mm    "
                f"轴距: {config.WHEELBASE_MM:.1f} mm    "
                f"轮距: {config.TRACK_MM:.1f} mm\\n"
                f"最大 vx/vy: {config.MAX_VX:.2f} / {config.MAX_VY:.2f} m/s    "
                f"最大 wz: {config.MAX_WZ:.2f} rad/s\\n"
                f"最小驱动: {config.MIN_DRIVE:.2f}    "
                f"加速度: {config.ACCEL_V:.2f} / {config.ACCEL_W:.2f}    "
                f"旋转轮速/90°时间: {config.ROTATE_DRIVE:.2f} / {config.ROTATE_MS_PER_90} ms\\n"
                f"位置 PID: Kp={config.DEFAULT_POS_KP:.2f} Ki={config.DEFAULT_POS_KI:.2f} "
                f"Kd={config.DEFAULT_POS_KD:.2f}    位置停容差: {config.POS_STOP_TOL_MM:.1f} mm")
        lbl_ov = QLabel(text)                              # 文本
        lbl_ov.setObjectName("sub")                        # 样式
        lbl_ov.setWordWrap(True)                           # 换行
        ol.addWidget(lbl_ov)                               # 加入
        layout.addWidget(ov)                               # 加入页面

        layout.addStretch(1)                               # 弹簧
        scroll.setWidget(page)                             # 设置页面
        return scroll                                      # 返回

'''
assert anchor in c
c = c.replace(anchor, method + anchor, 1)
open(p, "w", encoding="utf-8").write(c)
print("debug tab inserted")
