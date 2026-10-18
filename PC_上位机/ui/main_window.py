# -*- coding: utf-8 -*-
"""主窗口：连接、手动遥控、路线、PID调参、曲线、日志、预留Tab。"""

import datetime                                 # 时间戳
import time                                     # 时间
import math                                     # 数学
from PySide6.QtCore import Qt, QTimer           # Qt核心
from PySide6.QtGui import QFont                 # 字体
from PySide6.QtWidgets import (                 # 控件
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QGroupBox,
    QTabWidget, QPlainTextEdit, QSlider, QSpinBox, QDoubleSpinBox,
    QLineEdit, QFrame, QSizePolicy, QMessageBox
)
import serial.tools.list_ports                  # 枚举串口
import config                                   # 配置
import protocol                                 # 协议
from serial_worker import SerialWorker          # 串口线程
from demo_worker import DemoWorker              # 演示线程
from widgets.joystick import Joystick           # 虚拟摇杆
from widgets.curve_panel import CurvePanel      # 曲线面板


STYLE = """
QMainWindow, QWidget { background: #0E0F13; color: #E6E8EF; font-family: 'Microsoft YaHei'; font-size: 13px; }
QGroupBox { border: 1px solid #2A2D38; border-radius: 10px; margin-top: 14px; padding-top: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #00D1B2; }
QPushButton { background: #1B1D25; border: 1px solid #2A2D38; border-radius: 8px; padding: 8px 14px; color: #E6E8EF; }
QPushButton:hover { border-color: #00D1B2; color: #00D1B2; }
QPushButton:pressed { background: #00D1B2; color: #0E0F13; }
QPushButton#danger { background: #FF5C6C; color: #FFFFFF; font-weight: bold; }
QPushButton#accent { background: #00D1B2; color: #0E0F13; font-weight: bold; }
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit { background: #15161C; border: 1px solid #2A2D38; border-radius: 6px; padding: 6px; color: #E6E8EF; }
QTabWidget::pane { border: 1px solid #2A2D38; border-radius: 10px; }
QTabBar::tab { background: #15161C; color: #8A8F9E; padding: 10px 16px; margin-right: 4px; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { background: #1B1D25; color: #00D1B2; border-bottom: 2px solid #00D1B2; }
QPlainTextEdit { background: #0B0C10; border: 1px solid #2A2D38; border-radius: 8px; color: #C9CDD6; font-family: Consolas; }
QLabel#title { font-size: 20px; font-weight: bold; color: #FFFFFF; }
QLabel#sub { color: #8A8F9E; }
QLabel#value { color: #00D1B2; font-weight: bold; }
QLabel#dangerValue { color: #FF5C6C; font-weight: bold; }
QSlider::groove:horizontal { height: 6px; background: #2A2D38; border-radius: 3px; }
QSlider::handle:horizontal { width: 16px; margin: -5px 0; border-radius: 8px; background: #00D1B2; }
"""


class MainWindow(QMainWindow):
    """上位机主窗口。"""

    def __init__(self):
        super().__init__()                               # 父类初始化
        self.setWindowTitle(config.APP_NAME)             # 标题
        self.resize(config.WINDOW_W, config.WINDOW_H)    # 尺寸
        self.setStyleSheet(STYLE)                        # 应用黑色主题
        self.worker = None                               # 通信线程
        self.connected = False                           # 连接状态
        self.joy_x = 0.0                                 # 摇杆x
        self.joy_y = 0.0                                 # 摇杆y
        self.keys = set()                                # 按下的按键
        self.rotate_left = False                         # 左转标志
        self.rotate_right = False                        # 右转标志
        self.mode_name = "空闲"                          # 当前模式
        self.manual_pause_until = 0.0                    # 手动发送暂停截止时间
        self.route_active = False                         # 固定路线是否运行中
        self.route_step = 0                               # 当前边序号0-3
        self.route_gen = 0                                # 路线运行代号，用于作废旧定时器
        self.last_rx_time = 0.0                           # 最近收到数据的时间
        self.rx_bytes = 0                                 # 累计接收字节数
        self.link_test_pending = False                    # 是否在等待链路测试ACK
        self._build_ui()                                 # 构建界面
        self._refresh_ports()                            # 刷新串口
        self.timer = QTimer(self)                        # 手动控制定时器
        self.timer.timeout.connect(self._manual_tick)    # 定时发送
        self.timer.start(config.TX_INTERVAL_MS)          # 启动
        self.link_timer = QTimer(self)                    # 链路状态定时器
        self.link_timer.timeout.connect(self._update_link_status)   # 更新链路状态
        self.link_timer.start(1000)                       # 每秒更新
        self.setFocusPolicy(Qt.StrongFocus)              # 允许键盘

    # ================= 界面构建 =================
    def _build_ui(self):
        """构建主界面。"""
        central = QWidget()                              # 中央控件
        self.setCentralWidget(central)                   # 设置
        root = QHBoxLayout(central)                      # 水平布局
        root.setContentsMargins(16, 16, 16, 16)          # 边距
        root.setSpacing(14)                              # 间距
        root.addWidget(self._build_sidebar())            # 左侧栏
        self.tabs = QTabWidget()                         # Tab容器
        self.tabs.addTab(self._build_manual_tab(), "手动遥控")     # 手动
        self.tabs.addTab(self._build_route_tab(), "固定路线")      # 路线
        self.tabs.addTab(self._build_pid_tab(), "PID调参")         # PID
        self.tabs.addTab(self._build_curve_tab(), "数据曲线")      # 曲线
        self.tabs.addTab(self._build_log_tab(), "日志")            # 日志
        self.tabs.addTab(self._build_placeholder("自动驾驶"), "自动驾驶")   # 预留
        self.tabs.addTab(self._build_placeholder("避障"), "避障")           # 预留
        self.tabs.addTab(self._build_placeholder("视觉"), "视觉")           # 预留
        root.addWidget(self.tabs, 1)                     # 加入布局
        self.statusBar().showMessage("未连接")            # 状态栏

    def _build_sidebar(self):
        """左侧栏：连接、状态、急停。"""
        box = QWidget()                                  # 容器
        box.setFixedWidth(270)                           # 固定宽度
        layout = QVBoxLayout(box)                        # 垂直布局
        layout.setContentsMargins(0, 0, 0, 0)            # 无边距
        layout.setSpacing(12)                            # 间距
        title = QLabel(config.APP_NAME)                  # 标题
        title.setObjectName("title")                     # 样式名
        layout.addWidget(title)                          # 加入
        sub = QLabel("STM32F407 + 麦轮底盘")              # 副标题
        sub.setObjectName("sub")                         # 样式名
        layout.addWidget(sub)                            # 加入

        conn = QGroupBox("连接")                          # 连接分组
        cl = QVBoxLayout(conn)                            # 布局
        self.port_combo = QComboBox()                     # 端口下拉
        self.port_combo.setEditable(True)                 # 可编辑
        cl.addWidget(self.port_combo)                     # 加入
        bh = QHBoxLayout()                                 # 波特率行
        bh.addWidget(QLabel("波特率"))                      # 标签
        self.baud_combo = QComboBox()                      # 波特率下拉
        for b in config.BAUDRATE_OPTIONS:                  # 加入选项
            self.baud_combo.addItem(str(b))                # 添加
        self.baud_combo.setCurrentText(str(config.SERIAL_BAUDRATE))   # 默认
        bh.addWidget(self.baud_combo)                      # 加入
        cl.addLayout(bh)                                   # 加入连接分组
        self.port_combo.currentTextChanged.connect(self._on_port_changed)   # 端口变化自动匹配波特率
        h = QHBoxLayout()                                 # 水平
        self.btn_refresh = QPushButton("刷新")            # 刷新按钮
        self.btn_connect = QPushButton("连接")            # 连接按钮
        self.btn_connect.setObjectName("accent")          # 强调色
        h.addWidget(self.btn_refresh)                     # 加入
        h.addWidget(self.btn_connect)                     # 加入
        self.btn_link_test = QPushButton("测试链路")      # 链路测试
        h.addWidget(self.btn_link_test)                   # 加入
        cl.addLayout(h)                                   # 加入布局
        self.chk_demo = QCheckBox("演示模式（无硬件）")     # 演示模式
        cl.addWidget(self.chk_demo)                       # 加入
        self.lbl_conn = QLabel("● 未连接")                 # 连接状态
        self.lbl_conn.setStyleSheet("color:#8A8F9E;")     # 灰色
        cl.addWidget(self.lbl_conn)                       # 加入
        layout.addWidget(conn)                            # 加入左栏

        st = QGroupBox("状态")                            # 状态分组
        sl = QGridLayout(st)                              # 网格
        sl.addWidget(QLabel("模式"), 0, 0)                 # 模式标签
        self.lbl_mode = QLabel("--")                      # 模式值（未收到数据）
        self.lbl_mode.setObjectName("value")              # 样式
        sl.addWidget(self.lbl_mode, 0, 1)                 # 加入
        sl.addWidget(QLabel("电池"), 1, 0)                 # 电池标签
        self.lbl_batt = QLabel("-- mV")                   # 电池值
        sl.addWidget(self.lbl_batt, 1, 1)                 # 加入
        sl.addWidget(QLabel("A/B/C/D"), 2, 0)             # 轮速标签
        self.lbl_speed = QLabel("0.00 / 0.00 / 0.00 / 0.00")   # 轮速
        sl.addWidget(self.lbl_speed, 2, 1)                # 加入
        sl.addWidget(QLabel("编码器"), 3, 0)               # 编码器标签
        self.lbl_enc = QLabel("0 / 0 / 0 / 0")           # 编码器值
        sl.addWidget(self.lbl_enc, 3, 1)                  # 加入
        sl.addWidget(QLabel("接收"), 4, 0)                # 接收标签
        self.lbl_rx = QLabel("0 bytes")                   # 接收字节
        sl.addWidget(self.lbl_rx, 4, 1)                   # 加入
        layout.addWidget(st)                              # 加入左栏

        self.btn_estop = QPushButton("急停 STOP")         # 急停按钮
        self.btn_estop.setObjectName("danger")            # 红色
        self.btn_estop.setMinimumHeight(64)               # 高度
        layout.addWidget(self.btn_estop)                  # 加入
        self.btn_refresh.clicked.connect(self._refresh_ports)          # 刷新串口
        self.btn_connect.clicked.connect(self._toggle_connection)      # 连接/断开
        self.btn_link_test.clicked.connect(self._link_test)            # 测试链路
        self.btn_estop.clicked.connect(lambda: self._send(protocol.cmd_stop_all()))   # 急停
        layout.addStretch(1)                              # 弹簧
        hint = QLabel("快捷键：WASD 移动\nQ/E 原地旋转\n空格 急停")   # 快捷键提示
        hint.setObjectName("sub")                         # 样式
        layout.addWidget(hint)                            # 加入
        return box                                        # 返回

    def _build_manual_tab(self):
        """手动遥控Tab。"""
        page = QWidget()                                  # 页面
        layout = QHBoxLayout(page)                        # 水平布局
        layout.setContentsMargins(18, 18, 18, 18)         # 边距
        layout.setSpacing(20)                             # 间距
        self.joystick = Joystick()                        # 摇杆
        self.joystick.changed.connect(self._on_joystick)  # 连接信号
        layout.addWidget(self.joystick, 1)                # 加入
        right = QVBoxLayout()                             # 右侧布局
        right.setSpacing(12)                              # 间距

        lim = QGroupBox("速度限幅")                        # 限幅组
        ll = QGridLayout(lim)                             # 网格
        self.sl_vx, self.lbl_vx = self._add_slider(ll, 0, "前后 vx", config.MAX_VX, 0.1, 1.2)   # vx
        self.sl_vy, self.lbl_vy = self._add_slider(ll, 1, "左右 vy", config.MAX_VY, 0.1, 1.2)   # vy
        self.sl_wz, self.lbl_wz = self._add_slider(ll, 2, "旋转 wz", config.MAX_WZ, 0.2, 3.0)   # wz
        right.addWidget(lim)                              # 加入

        rot = QGroupBox("原地旋转 / 刹车")                  # 旋转刹车组
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
        return page                                       # 返回

    def _add_slider(self, grid, row, name, value, minimum, maximum):
        """添加一个带数值显示的滑块。"""
        grid.addWidget(QLabel(name), row, 0)              # 名称
        slider = QSlider(Qt.Horizontal)                   # 滑块
        slider.setRange(int(minimum * 100), int(maximum * 100))   # 范围
        slider.setValue(int(value * 100))                 # 默认值
        label = QLabel(f"{value:.2f}")                    # 数值
        label.setObjectName("value")                      # 样式
        grid.addWidget(slider, row, 1)                    # 加入
        grid.addWidget(label, row, 2)                     # 加入
        slider.valueChanged.connect(lambda v, l=label: l.setText(f"{v/100:.2f}"))   # 更新
        return slider, label                              # 返回

    def _build_route_tab(self):
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
        gl.addWidget(QLabel("停顿"), 2, 0)                 # 标签
        self.spin_route_pause = QSpinBox()                # 停顿时间
        self.spin_route_pause.setRange(0, 3000)           # 范围
        self.spin_route_pause.setValue(500)               # 默认500ms
        self.spin_route_pause.setSuffix(" ms")            # 单位
        gl.addWidget(self.spin_route_pause, 2, 1)         # 加入
        note = QLabel("前进 -> 停顿 -> 左转90° -> 停顿 -> 重复4次。")   # 说明
        note.setObjectName("sub")                         # 样式
        gl.addWidget(note, 3, 0, 1, 4)                    # 加入
        layout.addWidget(box)                             # 加入
        layout.addStretch(1)                              # 弹簧
        self.btn_route_start.clicked.connect(self._route_start)   # 开始
        self.btn_route_stop.clicked.connect(self._route_stop)     # 停止
        return page                                       # 返回

    def _route_start(self):
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

    def _build_pid_tab(self):
        """PID调参Tab。"""
        page = QWidget()                                  # 页面
        layout = QVBoxLayout(page)                        # 垂直
        layout.setContentsMargins(18, 18, 18, 18)         # 边距
        box = QGroupBox("位置环 PID（速度环由驱动模块内部完成）")   # 分组
        gl = QGridLayout(box)                             # 网格
        self.spin_kp = self._add_dspin(gl, 0, "Kp", config.DEFAULT_POS_KP)   # Kp
        self.spin_ki = self._add_dspin(gl, 1, "Ki", config.DEFAULT_POS_KI)   # Ki
        self.spin_kd = self._add_dspin(gl, 2, "Kd", config.DEFAULT_POS_KD)   # Kd
        gl.addWidget(QLabel("最大线速度"), 3, 0)           # 标签
        self.spin_vmax = QDoubleSpinBox()                 # 最大线速度
        self.spin_vmax.setRange(0.05, 2.0)                # 范围
        self.spin_vmax.setDecimals(2)                     # 小数
        self.spin_vmax.setValue(config.MAX_VX)            # 默认
        gl.addWidget(self.spin_vmax, 3, 1)                # 加入
        gl.addWidget(QLabel("最大角速度"), 4, 0)           # 标签
        self.spin_wmax = QDoubleSpinBox()                 # 最大角速度
        self.spin_wmax.setRange(0.1, 3.0)                 # 范围
        self.spin_wmax.setDecimals(2)                     # 小数
        self.spin_wmax.setValue(config.MAX_WZ)            # 默认
        gl.addWidget(self.spin_wmax, 4, 1)                # 加入
        h = QHBoxLayout()                                 # 按钮行
        self.btn_pid_apply = QPushButton("下发参数")        # 下发
        self.btn_pid_apply.setObjectName("accent")        # 强调
        self.btn_pid_read = QPushButton("读取参数")         # 读取
        h.addWidget(self.btn_pid_apply)                   # 加入
        h.addWidget(self.btn_pid_read)                    # 加入
        gl.addLayout(h, 5, 0, 1, 2)                       # 加入
        layout.addWidget(box)                             # 加入
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
        self.btn_pid_apply.clicked.connect(self._on_pid_apply)   # 下发
        self.btn_pid_read.clicked.connect(lambda: self._send(protocol.cmd_read_params()))   # 读取
        self.btn_accel_apply.clicked.connect(self._on_accel_apply)   # 下发平滑参数
        return page                                       # 返回

    def _add_dspin(self, grid, row, name, value):
        """添加一个double输入。"""
        grid.addWidget(QLabel(name), row, 0)              # 标签
        sp = QDoubleSpinBox()                             # 输入框
        sp.setRange(0.0, 20.0)                            # 范围
        sp.setDecimals(3)                                 # 小数位
        sp.setSingleStep(0.01)                            # 步进
        sp.setValue(value)                                # 默认
        grid.addWidget(sp, row, 1)                        # 加入
        return sp                                         # 返回

    def _build_curve_tab(self):
        """数据曲线Tab。"""
        page = QWidget()                                  # 页面
        layout = QVBoxLayout(page)                        # 垂直
        layout.setContentsMargins(12, 12, 12, 12)         # 边距
        self.curve_panel = CurvePanel()                   # 曲线面板
        layout.addWidget(self.curve_panel)                # 加入
        return page                                       # 返回

    def _build_log_tab(self):
        """日志Tab。"""
        page = QWidget()                                  # 页面
        layout = QVBoxLayout(page)                        # 垂直
        layout.setContentsMargins(12, 12, 12, 12)         # 边距
        self.log_view = QPlainTextEdit()                  # 日志框
        self.log_view.setReadOnly(True)                   # 只读
        layout.addWidget(self.log_view)                   # 加入
        btn = QPushButton("清空日志")                      # 清空按钮
        btn.clicked.connect(self.log_view.clear)          # 连接
        layout.addWidget(btn)                             # 加入
        return page                                       # 返回

    def _build_placeholder(self, name):
        """占位Tab。"""
        page = QWidget()                                  # 页面
        layout = QVBoxLayout(page)                        # 垂直
        label = QLabel(f"{name}（预留）\n\n该功能将在后续阶段接入。")   # 文字
        label.setAlignment(Qt.AlignCenter)                # 居中
        label.setObjectName("sub")                        # 样式
        layout.addWidget(label)                           # 加入
        return page                                       # 返回

    # ================= 连接 =================
    def _on_port_changed(self, port):
        """端口变化时自动匹配波特率。"""
        if port in config.PORT_BAUDRATE:               # 有指定波特率
            self.baud_combo.setCurrentText(str(config.PORT_BAUDRATE[port]))   # 设置

    def _refresh_ports(self):
        """刷新串口列表。"""
        self.port_combo.clear()                           # 清空
        ports = [p.device for p in serial.tools.list_ports.comports()]   # 枚举
        for p in config.PORT_CANDIDATES:                  # 候选优先
            if p not in ports:                            # 不存在也加上
                ports.append(p)
        for p in ports:                                   # 加入下拉
            self.port_combo.addItem(p)
        if config.DEFAULT_PORT in ports:                  # 默认端口
            self.port_combo.setCurrentText(config.DEFAULT_PORT)
        self._on_port_changed(self.port_combo.currentText())   # 自动匹配波特率

    def _toggle_connection(self):
        """连接/断开。"""
        if self.connected:                                # 已连接则断开
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        """建立连接。"""
        if self.chk_demo.isChecked():                     # 演示模式
            self.worker = DemoWorker()                    # 创建演示线程
            self._wire_worker()                           # 连接信号
            self.worker.start()                           # 启动
        else:
            port = self.port_combo.currentText().strip()  # 端口
            if not port:                                  # 没填
                self._log("请选择串口")                    # 提示
                return
            baud = int(self.baud_combo.currentText())     # 当前波特率
            self.worker = SerialWorker(port, baud)        # 创建串口线程
            self._wire_worker()                           # 连接信号
            self.worker.start()                           # 启动

    def _wire_worker(self):
        """连接线程信号。"""
        self.worker.connection_changed.connect(self._on_connection_changed)   # 连接状态
        self.worker.status_received.connect(self._on_status)                  # 状态
        self.worker.curve_received.connect(self._on_curve)                    # 曲线
        self.worker.ack_received.connect(self._on_ack)                        # ACK
        self.worker.params_received.connect(self._on_params)                  # 参数
        self.worker.log_received.connect(self._log)                           # 日志
        self.worker.tx_log.connect(lambda x: self._log(f"TX {x}"))            # 发送日志
        self.worker.rx_log.connect(lambda x: None)                            # 接收日志暂不显示
        self.worker.rx_activity.connect(self._on_rx_activity)                 # 接收活动

    def _disconnect(self):
        """断开连接。"""
        if self.worker:                                   # 有线程
            self.worker.stop()                            # 请求停止
            self.worker.wait(1000)                        # 等待
            self.worker = None                            # 清空
        self.connected = False                            # 状态
        self.lbl_conn.setText("● 未连接")                  # 更新
        self.lbl_conn.setStyleSheet("color:#8A8F9E;")     # 灰色
        self.btn_connect.setText("连接")                   # 按钮文字
        self.lbl_mode.setText("--")                        # 模式显示为空
        self.statusBar().showMessage("未连接")             # 状态栏

    def _on_connection_changed(self, ok, msg):
        """连接状态变化。"""
        self.connected = ok                               # 保存
        if ok:                                            # 已连接
            self.lbl_conn.setText(f"● {msg}")             # 显示
            self.lbl_conn.setStyleSheet("color:#00D1B2;") # 绿色
            self.btn_connect.setText("断开")               # 按钮
            self.statusBar().showMessage(msg)             # 状态栏
            self.last_rx_time = time.time()               # 重置接收时间
            self.rx_bytes = 0                             # 重置字节数
            self.lbl_rx.setText("0 bytes")                # 显示
            self._send(protocol.cmd_heartbeat())          # 发心跳
        else:                                             # 断开
            self.lbl_conn.setText(f"● {msg}")             # 显示
            self.lbl_conn.setStyleSheet("color:#FF5C6C;") # 红色
            self.btn_connect.setText("连接")               # 按钮
        self._log(msg)                                    # 日志

    # ================= 数据回调 =================
    def _on_status(self, data):
        """状态帧回调。"""
        names = {0: "空闲", 1: "手动", 2: "缓停", 3: "PID停", 4: "路线", 5: "旋转"}   # 模式名
        self.mode_name = names.get(data["mode"], "未知")   # 模式
        self.lbl_mode.setText(self.mode_name)             # 更新
        self.lbl_batt.setText(f"{data['battery']} mV")    # 电池
        self.lbl_speed.setText(" / ".join(f"{v:.2f}" for v in data["speed"]))   # 速度
        self.lbl_enc.setText(" / ".join(str(v) for v in data["enc"]))            # 编码器

    def _on_curve(self, data):
        """曲线帧回调。"""
        self.curve_panel.update_data(data["target"], data["actual"])   # 更新曲线

    def _on_ack(self, data):
        """ACK回调。"""
        self._log(f"ACK cmd=0x{data['cmd']:02X} err={data['err']}")   # 日志
        if self.link_test_pending and data["cmd"] == config.CMD_HEARTBEAT:   # 链路测试
            self.link_test_pending = False            # 清除等待
            self._log("链路测试成功：收到心跳ACK")     # 提示

    def _on_params(self, data):
        """参数帧回调。"""
        self.spin_kp.setValue(data["kp"])                 # Kp
        self.spin_ki.setValue(data["ki"])                 # Ki
        self.spin_kd.setValue(data["kd"])                 # Kd
        self.spin_vmax.setValue(data["vmax"])             # vmax
        self.spin_wmax.setValue(data["wmax"])             # wmax
        self._log("参数已读取")                            # 日志

    # ================= 控制 =================
    def _on_rx_activity(self, n):
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

    def _on_joystick(self, x, y):
        """摇杆变化。"""
        self.joy_x = x                                    # 保存
        self.joy_y = y                                    # 保存

    def _manual_tick(self):
        """周期发送手动速度。"""
        if not self.connected or self.worker is None:     # 未连接
            return
        if self.tabs.currentIndex() != 0:                 # 不在手动Tab
            return
        if self.route_active:                            # 路线运行中
            return
        if time.time() < self.manual_pause_until:        # 特殊指令后短暂暂停
            return
        jy = math.copysign(abs(self.joy_y) ** 0.7, self.joy_y) if self.joy_y else 0.0   # 灵敏度曲线
        jx = math.copysign(abs(self.joy_x) ** 0.7, self.joy_x) if self.joy_x else 0.0   # 灵敏度曲线
        vx = jy * (self.sl_vx.value() / 100.0)          # 摇杆前后
        vy = -jx * (self.sl_vy.value() / 100.0)         # 摇杆左右
        wz = 0.0                                          # 旋转
        if "W" in self.keys: vx += self.sl_vx.value() / 100.0   # 键盘前进
        if "S" in self.keys: vx -= self.sl_vx.value() / 100.0   # 键盘后退
        if "A" in self.keys: vy += self.sl_vy.value() / 100.0   # 键盘左移
        if "D" in self.keys: vy -= self.sl_vy.value() / 100.0   # 键盘右移
        if self.rotate_left: wz += self.sl_wz.value() / 100.0   # 左转
        if self.rotate_right: wz -= self.sl_wz.value() / 100.0  # 右转
        vx = max(-1.2, min(1.2, vx))                      # 限幅
        vy = max(-1.2, min(1.2, vy))                      # 限幅
        wz = max(-3.0, min(3.0, wz))                      # 限幅
        self._send(protocol.cmd_manual(vx, vy, wz))       # 发送

    def _rotate_angle(self, deg):
        """原地旋转指定角度（正=左转，负=右转）。"""
        self.manual_pause_until = time.time() + 2.0       # 暂停手动发送，避免打断旋转
        self._send(protocol.cmd_rotate(deg))              # 发送旋转指令
        self._log(f"原地旋转 {deg}°")                      # 日志

    def _special_send(self, frame, pause_s=0.5):
        """发送刹车/停止等特殊指令，并短暂暂停手动发送。"""
        self.manual_pause_until = time.time() + pause_s   # 暂停手动发送
        self._send(frame)                                 # 发送

    def _on_pid_stop(self):
        """PID精准停。"""
        self._send(protocol.cmd_pid_stop(self.spin_pid_mm.value()))   # 发送

    def _on_accel_apply(self):
        """下发加速度限制（速度平滑）。"""
        if self.chk_smooth.isChecked():                   # 启用平滑
            self._send(protocol.cmd_set_accel(self.spin_accel_v.value(),
                                              self.spin_accel_w.value()))
            self._log("已下发平滑参数")
        else:                                             # 关闭平滑
            self._send(protocol.cmd_set_accel(1000.0, 1000.0))
            self._log("已关闭平滑（急起急停）")

    def _on_pid_apply(self):
        """下发PID和限幅。"""
        self._send(protocol.cmd_set_pos_pid(self.spin_kp.value(),
                                            self.spin_ki.value(),
                                            self.spin_kd.value()))    # PID
        self._send(protocol.cmd_set_limits(self.spin_vmax.value(),
                                           self.spin_wmax.value()))  # 限幅
        self._log("PID与限幅已下发")                        # 日志

    def _send(self, frame):
        """发送一帧。"""
        if self.worker and self.connected:                 # 已连接
            self.worker.send_frame(frame)                  # 发送

    # ================= 键盘 =================
    def keyPressEvent(self, event):
        """按键按下。"""
        key = event.key()                                  # 键码
        if key == Qt.Key_Space:                            # 空格急停
            if self.worker and self.connected:             # 已连接
                self.worker.send_frame(protocol.cmd_stop_all())   # 急停
            return
        text = event.text().upper()                        # 文本
        if text in ("W", "A", "S", "D", "Q", "E"):         # 控制键
            self.keys.add(text)                            # 记录
            if text == "Q": self.rotate_left = True        # Q左转
            if text == "E": self.rotate_right = True       # E右转
        super().keyPressEvent(event)                       # 父类

    def keyReleaseEvent(self, event):
        """按键松开。"""
        text = event.text().upper()                        # 文本
        if text in ("W", "A", "S", "D", "Q", "E"):         # 控制键
            self.keys.discard(text)                        # 移除
            if text == "Q": self.rotate_left = False       # 停止左转
            if text == "E": self.rotate_right = False      # 停止右转
        super().keyReleaseEvent(event)                     # 父类

    # ================= 日志 =================
    def _log(self, text):
        """追加日志。"""
        now = datetime.datetime.now().strftime("%H:%M:%S") # 时间
        self.log_view.appendPlainText(f"[{now}] {text}")   # 追加

    def closeEvent(self, event):
        """关闭窗口时断开。"""
        self._disconnect()                                 # 断开
        event.accept()                                     # 接受关闭
