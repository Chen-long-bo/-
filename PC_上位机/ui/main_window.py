# -*- coding: utf-8 -*-
"""主窗口：按键遥控、固定路线、控制与测试、参数调节、曲线、日志。"""

import datetime                                 # 时间戳
import json                                     # 读取参数说明数据
import math                                     # 数学计算
import time                                     # 时间控制
from pathlib import Path                        # 文件路径
from PySide6.QtCore import Qt, QTimer           # Qt 核心
from PySide6.QtWidgets import (                 # 控件
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QGroupBox,
    QTabWidget, QPlainTextEdit, QSlider, QSpinBox, QDoubleSpinBox,
    QLineEdit, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)
import serial.tools.list_ports                  # 枚举串口
import config                                   # 上位机配置
import protocol                                 # 通信协议
from serial_worker import SerialWorker          # 串口线程
from demo_worker import DemoWorker              # 演示线程
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
QTableWidget { background: #0B0C10; alternate-background-color: #11161C; border: 1px solid #2A2D38; gridline-color: #232B35; color: #C9CDD6; }
QHeaderView::section { background: #15161C; color: #8A8F9E; border: 0; border-right: 1px solid #2A2D38; border-bottom: 1px solid #2A2D38; padding: 6px; }
QTableWidget::item { padding: 5px; }
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
        self.setWindowTitle(config.APP_NAME)             # 窗口标题
        self.resize(config.WINDOW_W, config.WINDOW_H)    # 默认尺寸
        self.setStyleSheet(STYLE)                        # 应用黑色主题
        self.worker = None                               # 通信线程
        self.connected = False                           # 连接状态
        self.keys = set()                                # 当前按下的 WASD
        self.manual_hold_direction = (0.0, 0.0)          # 按键按住的方向
        self.mode_name = "空闲"                          # 当前模式
        self.manual_pause_until = 0.0                    # 特殊指令后的暂停截止时间
        self.route_active = False                         # 路线是否运行
        self.route_step = 0                              # 当前路线边序号
        self.route_gen = 0                               # 路线运行代号
        self.last_rx_time = 0.0                          # 最近接收数据时间
        self.rx_bytes = 0                                # 累计接收字节数
        self.link_test_pending = False                   # 链路测试等待标志
        self.last_status = None                          # 最近状态帧
        self.calib_start_counts = None                   # CPR 标定起点
        self.pid_active = False                          # 控制与测试页是否运行 PID
        self.pid_start_counts = None                     # PID 控制起点计数
        self.pid_target_m = 0.0                          # PID 目标位置 m
        self.pid_actual_m = 0.0                          # PID 实际位置 m
        self.pid_error_mm = 0.0                           # PID 位置误差 mm
        self.pid_started_at = 0.0                        # PID 开始时间
        self.parameter_data = self._load_parameter_guide()   # 参数说明数据
        self._build_ui()                                 # 构建界面
        self._refresh_ports()                            # 刷新串口
        self.timer = QTimer(self)                        # 手动控制定时器
        self.timer.timeout.connect(self._manual_tick)    # 周期发送
        self.timer.start(config.TX_INTERVAL_MS)          # 启动定时器
        self.link_timer = QTimer(self)                   # 链路状态定时器
        self.link_timer.timeout.connect(self._update_link_status)   # 更新链路状态
        self.link_timer.start(1000)                      # 每秒更新
        self.setFocusPolicy(Qt.StrongFocus)              # 允许键盘事件

    def _build_ui(self):
        """构建主界面。"""
        central = QWidget()                              # 中央控件
        self.setCentralWidget(central)                   # 设置中央控件
        root = QHBoxLayout(central)                      # 水平布局
        root.setContentsMargins(16, 16, 16, 16)          # 外边距
        root.setSpacing(14)                              # 控件间距
        root.addWidget(self._build_sidebar())            # 左侧连接栏
        self.tabs = QTabWidget()                         # Tab 容器
        self.tabs.addTab(self._build_manual_tab(), "手动遥控")          # 手动页
        self.tabs.addTab(self._build_route_tab(), "固定路线")           # 路线页
        self.pid_tab_index = self.tabs.addTab(self._build_control_test_tab(), "控制与测试")   # PID 页
        self.tabs.addTab(self._build_curve_tab(), "数据曲线")           # 曲线页
        self.param_tab_index = self.tabs.addTab(self._build_parameter_tab(), "参数调节")      # 参数页
        self.tabs.addTab(self._build_debug_tab(), "调试中心")           # 调试页
        self.tabs.addTab(self._build_log_tab(), "日志")                 # 日志页
        self.tabs.addTab(self._build_placeholder("自动驾驶"), "自动驾驶")   # 预留页
        self.tabs.addTab(self._build_placeholder("避障"), "避障")           # 预留页
        self.tabs.addTab(self._build_placeholder("视觉"), "视觉")           # 预留页
        self.tabs.currentChanged.connect(self._on_tab_changed)       # Tab 切换
        root.addWidget(self.tabs, 1)                     # 加入 Tab
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
        layout.addWidget(title)                          # 加入标题
        sub = QLabel("STM32F407 + 麦轮底盘")              # 副标题
        sub.setObjectName("sub")                         # 样式名
        layout.addWidget(sub)                            # 加入副标题
        conn = QGroupBox("连接")                          # 连接分组
        cl = QVBoxLayout(conn)                            # 连接布局
        self.port_combo = QComboBox()                     # 端口下拉
        self.port_combo.setEditable(True)                 # 允许手动输入
        cl.addWidget(self.port_combo)                     # 加入端口
        bh = QHBoxLayout()                                 # 波特率行
        bh.addWidget(QLabel("波特率"))                      # 标签
        self.baud_combo = QComboBox()                      # 波特率下拉
        for baud in config.BAUDRATE_OPTIONS:               # 加入波特率选项
            self.baud_combo.addItem(str(baud))             # 添加选项
        self.baud_combo.setCurrentText(str(config.SERIAL_BAUDRATE))   # 默认波特率
        bh.addWidget(self.baud_combo)                      # 加入波特率
        cl.addLayout(bh)                                   # 加入连接分组
        self.port_combo.currentTextChanged.connect(self._on_port_changed)   # 端口变化
        h = QHBoxLayout()                                 # 按钮行
        self.btn_refresh = QPushButton("刷新")            # 刷新按钮
        self.btn_connect = QPushButton("连接")            # 连接按钮
        self.btn_connect.setObjectName("accent")          # 强调色
        self.btn_link_test = QPushButton("测试链路")      # 链路测试
        h.addWidget(self.btn_refresh)                     # 加入刷新
        h.addWidget(self.btn_connect)                     # 加入连接
        h.addWidget(self.btn_link_test)                   # 加入链路测试
        cl.addLayout(h)                                   # 加入按钮行
        self.chk_demo = QCheckBox("演示模式（无硬件）")     # 演示模式
        cl.addWidget(self.chk_demo)                       # 加入演示模式
        self.lbl_conn = QLabel("● 未连接")                 # 连接状态
        self.lbl_conn.setStyleSheet("color:#8A8F9E;")     # 灰色
        cl.addWidget(self.lbl_conn)                       # 加入连接状态
        layout.addWidget(conn)                            # 加入左侧栏
        st = QGroupBox("状态")                            # 状态分组
        sl = QGridLayout(st)                              # 状态网格
        sl.addWidget(QLabel("模式"), 0, 0)                 # 模式标签
        self.lbl_mode = QLabel("--")                      # 模式值
        self.lbl_mode.setObjectName("value")              # 样式
        sl.addWidget(self.lbl_mode, 0, 1)                 # 加入模式
        sl.addWidget(QLabel("电池"), 1, 0)                 # 电池标签
        self.lbl_batt = QLabel("-- mV")                   # 电池值
        sl.addWidget(self.lbl_batt, 1, 1)                 # 加入电池
        sl.addWidget(QLabel("速度"), 2, 0)                 # 速度标签
        self.lbl_speed = QLabel("--")                     # 速度值
        sl.addWidget(self.lbl_speed, 2, 1)                 # 加入速度
        sl.addWidget(QLabel("编码器"), 3, 0)               # 编码器标签
        self.lbl_enc = QLabel("--")                       # 编码器值
        sl.addWidget(self.lbl_enc, 3, 1)                  # 加入编码器
        sl.addWidget(QLabel("RX"), 4, 0)                   # RX 标签
        self.lbl_rx = QLabel("0 bytes")                   # RX 值
        sl.addWidget(self.lbl_rx, 4, 1)                   # 加入 RX
        layout.addWidget(st)                              # 加入状态分组
        self.btn_estop = QPushButton("急停 STOP")         # 急停按钮
        self.btn_estop.setObjectName("danger")            # 红色
        self.btn_estop.setMinimumHeight(64)               # 高度
        layout.addWidget(self.btn_estop)                  # 加入急停
        self.btn_refresh.clicked.connect(self._refresh_ports)          # 刷新
        self.btn_connect.clicked.connect(self._toggle_connection)      # 连接
        self.btn_link_test.clicked.connect(self._link_test)            # 测试链路
        self.btn_estop.clicked.connect(self._manual_stop)              # 急停
        layout.addStretch(1)                              # 弹簧
        hint = QLabel("WASD：按住移动，松开停止\nQ/E：按设定角度左/右转\n空格：急停")   # 快捷键提示
        hint.setObjectName("sub")                         # 样式
        layout.addWidget(hint)                            # 加入提示
        return box                                        # 返回左侧栏

    def _build_manual_tab(self):
        """手动遥控页：方向按键、速度滑块、角度旋转。"""
        page = QWidget()                                  # 页面
        layout = QHBoxLayout(page)                        # 水平布局
        layout.setContentsMargins(18, 18, 18, 18)         # 边距
        layout.setSpacing(20)                             # 间距
        direction_box = QGroupBox("按键遥控（按住移动，松开停止）")   # 方向组
        grid = QGridLayout(direction_box)                # 网格
        self.btn_forward = QPushButton("▲\n前进")         # 前进
        self.btn_back = QPushButton("▼\n后退")            # 后退
        self.btn_left = QPushButton("◀\n左移")            # 左移
        self.btn_right = QPushButton("▶\n右移")           # 右移
        self.btn_manual_stop = QPushButton("停止")        # 停止
        for button in (self.btn_forward, self.btn_back, self.btn_left, self.btn_right):   # 统一按钮高度
            button.setMinimumHeight(64)                  # 设置高度
        self.btn_manual_stop.setMinimumHeight(52)        # 停止高度
        grid.addWidget(self.btn_forward, 0, 1)           # 前进
        grid.addWidget(self.btn_left, 1, 0)              # 左移
        grid.addWidget(self.btn_manual_stop, 1, 1)       # 停止
        grid.addWidget(self.btn_right, 1, 2)             # 右移
        grid.addWidget(self.btn_back, 2, 1)              # 后退
        layout.addWidget(direction_box, 1)               # 加入方向组
        right = QVBoxLayout()                             # 右侧布局
        right.setSpacing(12)                              # 间距
        speed_box = QGroupBox("平移速度")                  # 速度组
        speed_grid = QGridLayout(speed_box)              # 速度网格
        self.sl_speed, self.lbl_speed_value = self._add_slider(speed_grid, 0, "速度", 0.30, 0.10, 1.00)   # 速度滑块
        right.addWidget(speed_box)                        # 加入速度组
        rotate_box = QGroupBox("原地旋转（时间控制，不使用 PID）")   # 旋转组
        rotate_grid = QGridLayout(rotate_box)            # 旋转网格
        rotate_grid.addWidget(QLabel("角度"), 0, 0)       # 角度标签
        self.spin_rot_angle = QDoubleSpinBox()           # 角度输入
        self.spin_rot_angle.setRange(0.1, 360.0)         # 角度范围
        self.spin_rot_angle.setDecimals(1)               # 一位小数
        self.spin_rot_angle.setSingleStep(1.0)           # 一度步进
        self.spin_rot_angle.setValue(90.0)               # 默认 90°
        self.spin_rot_angle.setSuffix(" °")              # 角度单位
        rotate_grid.addWidget(self.spin_rot_angle, 0, 1) # 加入角度
        self.btn_rot_left = QPushButton("左转指定角度")    # 左转
        self.btn_rot_right = QPushButton("右转指定角度")   # 右转
        rotate_grid.addWidget(self.btn_rot_left, 1, 0)   # 左转
        rotate_grid.addWidget(self.btn_rot_right, 1, 1)  # 右转
        quick = QHBoxLayout()                             # 快捷按钮行
        self.btn_rot_l45 = QPushButton("左45°")           # 左45
        self.btn_rot_r45 = QPushButton("右45°")           # 右45
        self.btn_rot_l90 = QPushButton("左90°")           # 左90
        self.btn_rot_r90 = QPushButton("右90°")           # 右90
        quick.addWidget(self.btn_rot_l45)                 # 加入左45
        quick.addWidget(self.btn_rot_r45)                 # 加入右45
        quick.addWidget(self.btn_rot_l90)                 # 加入左90
        quick.addWidget(self.btn_rot_r90)                 # 加入右90
        rotate_grid.addLayout(quick, 2, 0, 1, 2)          # 加入快捷按钮
        right.addWidget(rotate_box)                       # 加入旋转组
        stop_box = QGroupBox("停止")                       # 停止组
        stop_layout = QHBoxLayout(stop_box)               # 停止布局
        self.btn_stop_all = QPushButton("立即停止")        # 立即停止
        self.btn_stop_all.setObjectName("danger")         # 红色
        stop_layout.addWidget(self.btn_stop_all)          # 加入按钮
        right.addWidget(stop_box)                         # 加入停止组
        right.addStretch(1)                               # 弹簧
        layout.addLayout(right, 1)                        # 加入右侧布局
        self.btn_forward.pressed.connect(lambda: self._manual_button_pressed(1.0, 0.0))   # 前进按下
        self.btn_forward.released.connect(self._manual_button_released)                   # 前进松开
        self.btn_back.pressed.connect(lambda: self._manual_button_pressed(-1.0, 0.0))     # 后退按下
        self.btn_back.released.connect(self._manual_button_released)                      # 后退松开
        self.btn_left.pressed.connect(lambda: self._manual_button_pressed(0.0, 1.0))      # 左移按下
        self.btn_left.released.connect(self._manual_button_released)                      # 左移松开
        self.btn_right.pressed.connect(lambda: self._manual_button_pressed(0.0, -1.0))    # 右移按下
        self.btn_right.released.connect(self._manual_button_released)                     # 右移松开
        self.btn_manual_stop.clicked.connect(self._manual_stop)                           # 手动停止
        self.btn_stop_all.clicked.connect(self._manual_stop)                              # 立即停止
        self.btn_rot_left.clicked.connect(lambda: self._rotate_by_angle(1.0))             # 左转指定角度
        self.btn_rot_right.clicked.connect(lambda: self._rotate_by_angle(-1.0))           # 右转指定角度
        self.btn_rot_l45.clicked.connect(lambda: self._rotate_angle(45.0))                 # 左45
        self.btn_rot_r45.clicked.connect(lambda: self._rotate_angle(-45.0))                # 右45
        self.btn_rot_l90.clicked.connect(lambda: self._rotate_angle(90.0))                 # 左90
        self.btn_rot_r90.clicked.connect(lambda: self._rotate_angle(-90.0))                # 右90
        return page                                       # 返回手动页

    def _add_slider(self, grid, row, name, value, minimum, maximum):
        """添加一个带数值显示的滑块。"""
        grid.addWidget(QLabel(name), row, 0)              # 名称
        slider = QSlider(Qt.Horizontal)                   # 滑块
        slider.setRange(int(minimum * 100), int(maximum * 100))   # 范围
        slider.setValue(int(value * 100))                 # 默认值
        label = QLabel(f"{value:.2f}")                    # 数值
        label.setObjectName("value")                      # 样式
        grid.addWidget(slider, row, 1)                    # 加入滑块
        grid.addWidget(label, row, 2)                     # 加入数值
        slider.valueChanged.connect(lambda v, l=label: l.setText(f"{v/100:.2f}"))   # 更新显示
        return slider, label                              # 返回控件

    def _build_route_tab(self):
        """固定路线页：不使用 PID，也不使用缓起缓停。"""
        page = QWidget()                                  # 页面
        layout = QVBoxLayout(page)                        # 垂直布局
        layout.setContentsMargins(18, 18, 18, 18)         # 边距
        box = QGroupBox("正方形路线（1×1米内）")            # 路线组
        gl = QGridLayout(box)                             # 网格
        gl.addWidget(QLabel("边长"), 0, 0)                 # 边长标签
        self.spin_route = QSpinBox()                      # 边长输入
        self.spin_route.setRange(100, 1000)               # 边长范围
        self.spin_route.setValue(config.DEFAULT_ROUTE_SIDE_MM)   # 默认边长
        self.spin_route.setSuffix(" mm")                  # 单位
        gl.addWidget(self.spin_route, 0, 1)               # 加入边长
        gl.addWidget(QLabel("速度"), 0, 2)                 # 速度标签
        self.spin_route_speed = QDoubleSpinBox()          # 路线速度
        self.spin_route_speed.setRange(0.30, 1.00)        # 速度范围
        self.spin_route_speed.setDecimals(2)              # 小数
        self.spin_route_speed.setSingleStep(0.05)         # 步进
        self.spin_route_speed.setValue(0.40)              # 默认速度
        gl.addWidget(self.spin_route_speed, 0, 3)         # 加入速度
        self.btn_route_start = QPushButton("开始")         # 开始按钮
        self.btn_route_start.setObjectName("accent")      # 强调色
        self.btn_route_stop = QPushButton("停止")          # 停止按钮
        gl.addWidget(self.btn_route_start, 1, 0)          # 加入开始
        gl.addWidget(self.btn_route_stop, 1, 1)           # 加入停止
        self.lbl_route_progress = QLabel("未开始")         # 路线进度
        self.lbl_route_progress.setObjectName("value")    # 样式
        gl.addWidget(self.lbl_route_progress, 1, 2, 1, 2) # 加入进度
        gl.addWidget(QLabel("停顿"), 2, 0)                 # 停顿标签
        self.spin_route_pause = QSpinBox()                # 停顿输入
        self.spin_route_pause.setRange(0, 3000)           # 停顿范围
        self.spin_route_pause.setValue(500)               # 默认停顿
        self.spin_route_pause.setSuffix(" ms")            # 单位
        gl.addWidget(self.spin_route_pause, 2, 1)         # 加入停顿
        note = QLabel("前进 -> 停顿 -> 左转90° -> 停顿 -> 重复4次。普通路线不使用 PID。")   # 说明
        note.setObjectName("sub")                         # 样式
        gl.addWidget(note, 3, 0, 1, 4)                    # 加入说明
        layout.addWidget(box)                             # 加入路线组
        layout.addStretch(1)                              # 弹簧
        self.btn_route_start.clicked.connect(self._route_start)   # 开始路线
        self.btn_route_stop.clicked.connect(self._route_stop)     # 停止路线
        return page                                       # 返回路线页

    def _route_start(self):
        """启动正方形路线。"""
        if self.route_active:                             # 已在运行
            return                                        # 不重复启动
        if not (self.worker and self.connected):          # 未连接
            self._log("请先连接小车")                      # 提示
            return                                        # 结束
        self.route_gen += 1                               # 新运行代号
        self.route_active = True                          # 标记运行
        self.route_step = 0                               # 从第一条边开始
        self.manual_pause_until = time.time() + 3600.0    # 暂停手动发送
        self.lbl_route_progress.setText("准备前进...")      # 显示准备
        self._route_forward(self.route_gen)               # 开始第一条边

    def _route_forward(self, gen):
        """路线：前进一条边。"""
        if gen != self.route_gen or not self.route_active:   # 旧定时器
            return                                        # 直接返回
        speed = self.spin_route_speed.value()             # 路线速度
        side_m = self.spin_route.value() / 1000.0         # 边长 m
        ms = max(300, int(side_m / speed * 1000))         # 前进时间
        self._send(protocol.cmd_manual(speed, 0.0, 0.0))  # 直接发速度
        self.lbl_route_progress.setText(f"第 {self.route_step+1}/4 边：前进 {side_m:.2f} m")   # 更新进度
        QTimer.singleShot(ms, lambda: self._route_pause_after_forward(gen))   # 前进结束

    def _route_pause_after_forward(self, gen):
        """前进后停顿。"""
        if gen != self.route_gen or not self.route_active:   # 旧定时器
            return                                        # 直接返回
        self._send(protocol.cmd_stop_all())               # 立即停车
        self.lbl_route_progress.setText(f"第 {self.route_step+1}/4 边：停顿")   # 更新进度
        QTimer.singleShot(self.spin_route_pause.value(), lambda: self._route_turn(gen))   # 停顿结束

    def _route_turn(self, gen):
        """路线：左转 90°。"""
        if gen != self.route_gen or not self.route_active:   # 旧定时器
            return                                        # 直接返回
        self._send(protocol.cmd_rotate(90.0))             # 时间控制左转
        self.lbl_route_progress.setText(f"第 {self.route_step+1}/4 边：左转90°")   # 更新进度
        QTimer.singleShot(1200, lambda: self._route_pause_after_turn(gen))   # 等待转向

    def _route_pause_after_turn(self, gen):
        """转向后停顿。"""
        if gen != self.route_gen or not self.route_active:   # 旧定时器
            return                                        # 直接返回
        self.lbl_route_progress.setText(f"第 {self.route_step+1}/4 边：停顿")   # 更新进度
        QTimer.singleShot(self.spin_route_pause.value(), lambda: self._route_next(gen))   # 停顿结束

    def _route_next(self, gen):
        """进入下一条边。"""
        if gen != self.route_gen or not self.route_active:   # 旧定时器
            return                                        # 直接返回
        self.route_step += 1                              # 边序号加一
        if self.route_step >= 4:                          # 四条边完成
            self._route_finish()                          # 完成路线
        else:                                             # 还有边
            self._route_forward(gen)                      # 下一条边

    def _route_finish(self):
        """路线完成。"""
        self.route_gen += 1                               # 作废旧定时器
        self.route_active = False                         # 清除运行标志
        self._send(protocol.cmd_stop_all())               # 停车
        self.manual_pause_until = 0.0                     # 恢复手动
        self.lbl_route_progress.setText("完成")            # 更新进度
        self._log("正方形路线完成")                        # 记录日志

    def _route_stop(self):
        """停止路线。"""
        self.route_gen += 1                               # 作废旧定时器
        self.route_active = False                         # 清除运行标志
        self._send(protocol.cmd_stop_all())               # 停车
        self.manual_pause_until = 0.0                     # 恢复手动
        self.lbl_route_progress.setText("已停止")          # 更新进度
        self._log("路线已停止")                            # 记录日志

    def _build_control_test_tab(self):
        """控制与测试页：只有本页使用 PID。"""
        scroll = QScrollArea()                             # 滚动区
        scroll.setWidgetResizable(True)                    # 自适应
        page = QWidget()                                   # 页面
        layout = QVBoxLayout(page)                         # 垂直布局
        layout.setContentsMargins(18, 18, 18, 18)          # 边距
        layout.setSpacing(12)                              # 间距
        control = QGroupBox("PID 位置控制（仅本页使用 PID）")   # PID 控制组
        grid = QGridLayout(control)                        # 网格
        self.spin_kp = self._add_dspin(grid, 0, "Kp", config.DEFAULT_POS_KP)   # Kp
        self.spin_ki = self._add_dspin(grid, 1, "Ki", config.DEFAULT_POS_KI)   # Ki
        self.spin_kd = self._add_dspin(grid, 2, "Kd", config.DEFAULT_POS_KD)   # Kd
        grid.addWidget(QLabel("目标距离"), 3, 0)           # 目标距离标签
        self.spin_pid_mm = QSpinBox()                      # 目标距离输入
        self.spin_pid_mm.setRange(-5000, 5000)             # 目标范围
        self.spin_pid_mm.setValue(300)                     # 默认 300mm
        self.spin_pid_mm.setSuffix(" mm")                  # 单位
        grid.addWidget(self.spin_pid_mm, 3, 1)             # 加入目标
        self.btn_pid_apply = QPushButton("下发参数")        # 下发参数按钮
        self.btn_pid_apply.setObjectName("accent")         # 强调色
        self.btn_pid_read = QPushButton("读取参数")         # 读取参数按钮
        self.btn_pid_start = QPushButton("开始 PID 位置控制")   # 开始按钮
        self.btn_pid_start.setObjectName("accent")         # 强调色
        self.btn_pid_abort = QPushButton("停止控制")        # 停止按钮
        button_row = QHBoxLayout()                         # 按钮行
        button_row.addWidget(self.btn_pid_apply)           # 加入下发
        button_row.addWidget(self.btn_pid_read)            # 加入读取
        button_row.addWidget(self.btn_pid_start)           # 加入开始
        button_row.addWidget(self.btn_pid_abort)           # 加入停止
        grid.addLayout(button_row, 4, 0, 1, 2)             # 加入按钮行
        layout.addWidget(control)                          # 加入控制组
        status = QGroupBox("PID 实时状态")                 # PID 状态组
        status_grid = QGridLayout(status)                  # 状态网格
        status_grid.addWidget(QLabel("目标位置"), 0, 0)     # 目标标签
        self.lbl_pid_target = QLabel("-- mm")              # 目标值
        self.lbl_pid_target.setObjectName("value")         # 样式
        status_grid.addWidget(self.lbl_pid_target, 0, 1)   # 加入目标
        status_grid.addWidget(QLabel("实际位置"), 1, 0)     # 实际标签
        self.lbl_pid_actual = QLabel("-- mm")              # 实际值
        self.lbl_pid_actual.setObjectName("value")         # 样式
        status_grid.addWidget(self.lbl_pid_actual, 1, 1)   # 加入实际
        status_grid.addWidget(QLabel("位置误差"), 2, 0)     # 误差标签
        self.lbl_pid_error = QLabel("-- mm")               # 误差值
        self.lbl_pid_error.setObjectName("dangerValue")    # 样式
        status_grid.addWidget(self.lbl_pid_error, 2, 1)    # 加入误差
        self.lbl_pid_state = QLabel("未运行")              # 运行状态
        self.lbl_pid_state.setObjectName("sub")            # 样式
        status_grid.addWidget(self.lbl_pid_state, 3, 0, 1, 2)   # 加入状态
        layout.addWidget(status)                           # 加入状态组
        note = QLabel("说明：普通手动、固定路线和旋转都不使用 PID；只有本页的“开始 PID 位置控制”会使用上面的 Kp/Ki/Kd。")   # 说明
        note.setObjectName("sub")                          # 样式
        note.setWordWrap(True)                             # 自动换行
        layout.addWidget(note)                             # 加入说明
        self.pid_curve_panel = CurvePanel()                # 控制页专用曲线
        layout.addWidget(self.pid_curve_panel, 1)          # 加入曲线
        self.btn_pid_apply.clicked.connect(self._on_pid_apply)    # 下发参数
        self.btn_pid_read.clicked.connect(self._on_pid_read)      # 读取参数
        self.btn_pid_start.clicked.connect(self._on_pid_start)    # 开始 PID
        self.btn_pid_abort.clicked.connect(self._on_pid_abort)    # 停止 PID
        self.spin_pid_mm.valueChanged.connect(lambda value: self.lbl_pid_target.setText(f"{value} mm"))   # 更新目标显示
        scroll.setWidget(page)                             # 设置滚动内容
        return scroll                                      # 返回控制页

    def _add_dspin(self, grid, row, name, value):
        """添加一个 PID 参数输入框。"""
        grid.addWidget(QLabel(name), row, 0)              # 参数标签
        spin = QDoubleSpinBox()                           # 输入框
        spin.setRange(0.0, 20.0)                          # 参数范围
        spin.setDecimals(3)                               # 小数位
        spin.setSingleStep(0.01)                          # 步进
        spin.setValue(value)                              # 默认值
        grid.addWidget(spin, row, 1)                      # 加入输入框
        return spin                                       # 返回输入框

    def _build_curve_tab(self):
        """数据曲线页：显示速度和 PID 位置/误差。"""
        page = QWidget()                                  # 页面
        layout = QVBoxLayout(page)                        # 垂直布局
        layout.setContentsMargins(12, 12, 12, 12)         # 边距
        self.curve_panel = CurvePanel()                   # 曲线面板
        layout.addWidget(self.curve_panel)                # 加入曲线
        return page                                       # 返回页面

    def _build_parameter_tab(self):
        """参数调节页：参数表、运行期修改、待确认假设。"""
        scroll = QScrollArea()                             # 滚动区
        scroll.setWidgetResizable(True)                    # 自适应
        page = QWidget()                                   # 页面
        layout = QVBoxLayout(page)                         # 垂直布局
        layout.setContentsMargins(16, 16, 16, 16)          # 边距
        layout.setSpacing(12)                              # 间距
        intro = QLabel("所有控制相关参数集中在这里。编译期参数需要 Keil 重新编译烧录；运行期参数可以立即下发。")   # 说明
        intro.setObjectName("sub")                         # 样式
        intro.setWordWrap(True)                            # 换行
        layout.addWidget(intro)                            # 加入说明
        runtime = QGroupBox("运行期参数快速修改")           # 运行期参数组
        runtime_grid = QGridLayout(runtime)                # 网格
        self.param_kp = self._add_dspin(runtime_grid, 0, "Kp", config.DEFAULT_POS_KP)   # Kp
        self.param_ki = self._add_dspin(runtime_grid, 1, "Ki", config.DEFAULT_POS_KI)   # Ki
        self.param_kd = self._add_dspin(runtime_grid, 2, "Kd", config.DEFAULT_POS_KD)   # Kd
        runtime_grid.addWidget(QLabel("最大线速度"), 0, 2)   # 线速度标签
        self.param_vmax = QDoubleSpinBox()                 # 最大线速度
        self.param_vmax.setRange(0.05, 2.0)                # 范围
        self.param_vmax.setDecimals(2)                     # 小数
        self.param_vmax.setValue(config.MAX_VX)            # 默认值
        runtime_grid.addWidget(self.param_vmax, 0, 3)      # 加入线速度
        runtime_grid.addWidget(QLabel("最大角速度"), 1, 2)  # 角速度标签
        self.param_wmax = QDoubleSpinBox()                 # 最大角速度
        self.param_wmax.setRange(0.1, 3.0)                 # 范围
        self.param_wmax.setDecimals(2)                     # 小数
        self.param_wmax.setValue(config.MAX_WZ)            # 默认值
        runtime_grid.addWidget(self.param_wmax, 1, 3)      # 加入角速度
        btn_apply = QPushButton("下发运行期参数")           # 下发按钮
        btn_apply.setObjectName("accent")                  # 强调色
        btn_read = QPushButton("读取当前参数")              # 读取按钮
        runtime_grid.addWidget(btn_apply, 2, 0, 1, 2)      # 加入下发
        runtime_grid.addWidget(btn_read, 2, 2, 1, 2)       # 加入读取
        btn_apply.clicked.connect(self._param_apply)       # 连接下发
        btn_read.clicked.connect(self._param_read)         # 连接读取
        layout.addWidget(runtime)                          # 加入运行期组
        table_box = QGroupBox("全部控制参数与调参方法")     # 参数表组
        table_layout = QVBoxLayout(table_box)              # 参数表布局
        filter_row = QHBoxLayout()                         # 筛选行
        self.param_search = QLineEdit()                    # 搜索框
        self.param_search.setPlaceholderText("搜索参数名、含义、影响、测试方法…")   # 占位提示
        self.param_kind = QComboBox()                      # 类型筛选
        self.param_kind.addItem("全部")                    # 全部类型
        kinds = sorted({row.get("kind", "") for row in self.parameter_data.get("parameters", [])})   # 收集类型
        for kind in kinds:                                 # 加入类型
            if kind:                                       # 跳过空类型
                self.param_kind.addItem(kind)              # 添加类型
        filter_row.addWidget(self.param_search, 1)         # 加入搜索
        filter_row.addWidget(self.param_kind)              # 加入类型
        table_layout.addLayout(filter_row)                 # 加入筛选行
        self.param_table = QTableWidget(0, 10)             # 参数表
        self.param_table.setHorizontalHeaderLabels([       # 表头
            "参数", "当前值", "单位", "类型", "位置", "含义",
            "调大影响", "调小影响", "测试/调参方法", "范围与风险",
        ])
        self.param_table.setEditTriggers(QAbstractItemView.NoEditTriggers)   # 只读
        self.param_table.setAlternatingRowColors(True)     # 交替背景
        self.param_table.setWordWrap(True)                 # 自动换行
        self.param_table.verticalHeader().setVisible(False)   # 隐藏行号
        self.param_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)   # 列宽自适应内容
        self.param_table.horizontalHeader().setStretchLastSection(True)   # 最后一列拉伸
        self.param_table.setMinimumHeight(420)             # 最小高度
        table_layout.addWidget(self.param_table)           # 加入表格
        layout.addWidget(table_box)                        # 加入参数表组
        self.param_search.textChanged.connect(self._render_parameter_table)   # 搜索变化
        self.param_kind.currentTextChanged.connect(self._render_parameter_table)   # 类型变化
        self._render_parameter_table()                     # 首次渲染
        assumptions = QGroupBox("待确认假设（不要替我猜）")   # 假设组
        assumptions_layout = QVBoxLayout(assumptions)      # 假设布局
        self.assumption_view = QPlainTextEdit()            # 假设文本框
        self.assumption_view.setReadOnly(True)             # 只读
        self.assumption_view.setPlainText(self._format_assumptions())   # 写入假设
        assumptions_layout.addWidget(self.assumption_view) # 加入假设
        layout.addWidget(assumptions)                      # 加入假设组
        layout.addStretch(1)                               # 弹簧
        scroll.setWidget(page)                             # 设置滚动内容
        return scroll                                      # 返回参数页

    def _load_parameter_guide(self):
        """读取参数说明 JSON；失败时返回空结构。"""
        path = Path(__file__).resolve().parents[1] / "parameter_guide.json"   # JSON 路径
        try:
            with path.open("r", encoding="utf-8-sig") as handle:   # 打开 JSON
                return json.load(handle)                   # 返回数据
        except Exception:
            return {"parameters": [], "assumptions": []}   # 返回空结构

    def _render_parameter_table(self):
        """按搜索词和类型刷新参数表。"""
        if not hasattr(self, "param_table"):               # 表格还没创建
            return                                        # 直接返回
        query = self.param_search.text().strip().lower()   # 搜索词
        kind = self.param_kind.currentText()               # 类型筛选
        rows = self.parameter_data.get("parameters", [])   # 全部参数
        filtered = []                                      # 过滤结果
        for row in rows:                                   # 遍历参数
            text = " ".join(str(row.get(key, "")) for key in ("name", "meaning", "increase", "decrease", "test", "warning", "source"))   # 搜索文本
            if query and query not in text.lower():        # 不匹配搜索
                continue                                  # 跳过
            if kind != "全部" and row.get("kind") != kind: # 类型不匹配
                continue                                  # 跳过
            filtered.append(row)                          # 加入结果
        self.param_table.setRowCount(len(filtered))        # 设置行数
        for r, row in enumerate(filtered):                 # 逐行填充
            values = [                                     # 列内容
                row.get("name", ""), row.get("value", ""), row.get("unit", ""),
                row.get("kind", ""), row.get("source", ""), row.get("meaning", ""),
                row.get("increase", ""), row.get("decrease", ""), row.get("test", ""),
                f"{row.get('range', '')}；{row.get('warning', '')}",
            ]
            for c, value in enumerate(values):             # 逐列填充
                item = QTableWidgetItem(str(value))        # 创建单元格
                item.setToolTip(str(value))                # 鼠标提示完整内容
                self.param_table.setItem(r, c, item)       # 设置单元格
        self.param_table.resizeRowsToContents()            # 自适应行高

    def _format_assumptions(self):
        """把待确认假设格式化为可读文本。"""
        lines = []                                         # 文本行
        for index, item in enumerate(self.parameter_data.get("assumptions", []), 1):   # 遍历假设
            lines.append(f"{index}. {item.get('item', '')}")   # 标题
            lines.append(f"   当前假设：{item.get('current', '')}")   # 当前假设
            lines.append(f"   确认方法：{item.get('confirm', '')}")   # 确认方法
            lines.append(f"   影响：{item.get('impact', '')}")       # 影响
            lines.append("")                                # 空行
        return "\n".join(lines) if lines else "暂无参数说明数据。"   # 返回文本

    def _build_debug_tab(self):
        """调试中心：链路、原始帧、编码器标定、旋转标定、点动和运动学预览。"""
        scroll = QScrollArea()                             # 滚动区
        scroll.setWidgetResizable(True)                    # 内容自适应
        page = QWidget()                                   # 页面容器
        layout = QVBoxLayout(page)                         # 垂直布局
        layout.setContentsMargins(16, 16, 16, 16)          # 边距
        layout.setSpacing(12)                              # 间距

        link = QGroupBox("链路状态")                        # 链路状态组
        ll = QVBoxLayout(link)                             # 垂直布局
        self.lbl_dbg_link = QLabel("未连接")               # 链路文字
        self.lbl_dbg_rx = QLabel("RX: 0 bytes")           # RX 统计
        ll.addWidget(self.lbl_dbg_link)                    # 加入链路文字
        ll.addWidget(self.lbl_dbg_rx)                      # 加入 RX
        lh = QHBoxLayout()                                 # 按钮行
        b_test = QPushButton("测试链路")                   # 链路测试按钮
        b_test.clicked.connect(self._link_test)            # 连接信号
        b_heart = QPushButton("发送心跳")                  # 心跳按钮
        b_heart.clicked.connect(lambda: self._send(protocol.cmd_heartbeat()))   # 发送心跳
        lh.addWidget(b_test)                               # 加入测试
        lh.addWidget(b_heart)                              # 加入心跳
        ll.addLayout(lh)                                   # 加入按钮行
        layout.addWidget(link)                             # 加入页面

        raw = QGroupBox("原始帧发送")                       # 原始帧组
        rl = QHBoxLayout(raw)                              # 水平布局
        self.edit_raw = QLineEdit()                        # 十六进制输入
        self.edit_raw.setPlaceholderText("AA 55 01 0A 0B") # 占位提示
        b_raw = QPushButton("发送十六进制")                # 发送按钮
        b_raw.clicked.connect(self._send_raw_frame)        # 连接发送
        rl.addWidget(self.edit_raw)                        # 加入输入
        rl.addWidget(b_raw)                                # 加入按钮
        layout.addWidget(raw)                              # 加入页面

        cal = QGroupBox("编码器 CPR 标定")                 # CPR 标定组
        cl = QGridLayout(cal)                              # 网格布局
        self.lbl_dbg_cpr = QLabel(f"当前 CPR: {config.ENCODER_CPR:.0f}")   # 当前 CPR
        self.lbl_dbg_enc = QLabel("计数: --")              # 当前计数
        cl.addWidget(self.lbl_dbg_cpr, 0, 0, 1, 2)         # 加入 CPR
        cl.addWidget(self.lbl_dbg_enc, 1, 0, 1, 2)         # 加入计数
        cl.addWidget(QLabel("实际行驶距离"), 2, 0)          # 距离标签
        self.spin_calib_mm = QDoubleSpinBox()              # 距离输入
        self.spin_calib_mm.setRange(10, 5000)              # 范围
        self.spin_calib_mm.setDecimals(1)                  # 小数位
        self.spin_calib_mm.setValue(1000)                  # 默认 1000mm
        self.spin_calib_mm.setSuffix(" mm")                # 单位
        cl.addWidget(self.spin_calib_mm, 2, 1)             # 加入距离
        b_start = QPushButton("记录起点")                  # 记录起点
        b_start.clicked.connect(self._calib_record_start)  # 连接
        b_calc = QPushButton("记录终点并计算")             # 计算按钮
        b_calc.clicked.connect(self._calib_compute_cpr)    # 连接
        cl.addWidget(b_start, 3, 0)                        # 加入起点
        cl.addWidget(b_calc, 3, 1)                         # 加入计算
        self.lbl_calib_result = QLabel("建议 CPR: --")     # 结果
        self.lbl_calib_result.setObjectName("value")       # 样式
        cl.addWidget(self.lbl_calib_result, 4, 0, 1, 2)    # 加入结果
        layout.addWidget(cal)                              # 加入页面

        rot = QGroupBox("原地旋转时间标定")                # 旋转标定组
        rl2 = QGridLayout(rot)                             # 网格布局
        self.lbl_rot_result = QLabel(f"当前 90° 时间: {config.ROTATE_MS_PER_90} ms")   # 当前值
        rl2.addWidget(self.lbl_rot_result, 0, 0, 1, 2)     # 加入当前值
        rl2.addWidget(QLabel("实测角度"), 1, 0)             # 角度标签
        self.spin_calib_deg = QDoubleSpinBox()             # 角度输入
        self.spin_calib_deg.setRange(1, 360)               # 范围
        self.spin_calib_deg.setDecimals(1)                 # 小数
        self.spin_calib_deg.setValue(90)                   # 默认
        self.spin_calib_deg.setSuffix(" °")                # 单位
        rl2.addWidget(self.spin_calib_deg, 1, 1)           # 加入角度
        b_90 = QPushButton("发送 90°")                     # 发送 90° 按钮
        b_90.clicked.connect(self._rotate_calib_send)      # 连接
        b_calc2 = QPushButton("计算建议时间")              # 计算按钮
        b_calc2.clicked.connect(self._rotate_calib_compute) # 连接
        rl2.addWidget(b_90, 2, 0)                          # 加入发送
        rl2.addWidget(b_calc2, 2, 1)                       # 加入计算
        layout.addWidget(rot)                              # 加入页面

        mot = QGroupBox("运动点动（短脉冲 600ms）")         # 点动组
        ml = QGridLayout(mot)                              # 网格布局
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
        ml.addWidget(self.btn_dbg_forward, 0, 0)           # 加入前进
        ml.addWidget(self.btn_dbg_back, 0, 1)              # 加入后退
        ml.addWidget(self.btn_dbg_left, 1, 0)              # 加入左移
        ml.addWidget(self.btn_dbg_right, 1, 1)             # 加入右移
        ml.addWidget(self.btn_dbg_rot_l, 2, 0)             # 加入左转
        ml.addWidget(self.btn_dbg_rot_r, 2, 1)             # 加入右转
        layout.addWidget(mot)                              # 加入页面

        geo = QGroupBox("【算法】麦轮逆运动学预览")        # 几何预览组
        gl = QGridLayout(geo)                              # 网格布局
        gl.addWidget(QLabel("vx"), 0, 0)                   # vx 标签
        self.spin_geo_vx = QDoubleSpinBox()                # vx 输入
        self.spin_geo_vx.setRange(-1.0, 1.0)               # 范围
        self.spin_geo_vx.setDecimals(2)                    # 小数
        self.spin_geo_vx.setValue(0.3)                     # 默认
        gl.addWidget(self.spin_geo_vx, 0, 1)               # 加入 vx
        gl.addWidget(QLabel("vy"), 1, 0)                   # vy 标签
        self.spin_geo_vy = QDoubleSpinBox()                # vy 输入
        self.spin_geo_vy.setRange(-1.0, 1.0)               # 范围
        self.spin_geo_vy.setDecimals(2)                    # 小数
        self.spin_geo_vy.setValue(0.0)                     # 默认
        gl.addWidget(self.spin_geo_vy, 1, 1)               # 加入 vy
        gl.addWidget(QLabel("wz"), 2, 0)                   # wz 标签
        self.spin_geo_wz = QDoubleSpinBox()                # wz 输入
        self.spin_geo_wz.setRange(-2.0, 2.0)               # 范围
        self.spin_geo_wz.setDecimals(2)                    # 小数
        self.spin_geo_wz.setValue(0.0)                     # 默认
        gl.addWidget(self.spin_geo_wz, 2, 1)               # 加入 wz
        b_geo = QPushButton("计算四轮速度")                # 计算按钮
        b_geo.clicked.connect(self._geo_compute)           # 连接
        gl.addWidget(b_geo, 3, 0, 1, 2)                    # 加入按钮
        self.lbl_geo = QLabel("A/B/C/D: --")               # 结果
        self.lbl_geo.setObjectName("value")                # 样式
        self.lbl_geo.setWordWrap(True)                     # 自动换行
        gl.addWidget(self.lbl_geo, 4, 0, 1, 2)             # 加入结果
        layout.addWidget(geo)                              # 加入页面
        layout.addStretch(1)                               # 弹簧
        scroll.setWidget(page)                             # 设置页面
        return scroll                                      # 返回调试页

    def _build_log_tab(self):
        """日志页。"""
        page = QWidget()                                   # 页面
        layout = QVBoxLayout(page)                         # 垂直布局
        layout.setContentsMargins(12, 12, 12, 12)          # 边距
        self.log_view = QPlainTextEdit()                   # 日志文本框
        self.log_view.setReadOnly(True)                    # 只读
        self.log_view.setMaximumBlockCount(2000)           # 限制历史长度
        layout.addWidget(self.log_view)                    # 加入日志框
        return page                                        # 返回日志页

    def _build_placeholder(self, name):
        """预留页。"""
        page = QWidget()                                   # 页面
        layout = QVBoxLayout(page)                         # 垂直布局
        label = QLabel(f"{name}\n\n接口已预留，后续接入对应传感器和算法。")   # 提示
        label.setObjectName("sub")                         # 样式
        label.setAlignment(Qt.AlignCenter)                 # 居中
        layout.addWidget(label)                            # 加入提示
        return page                                        # 返回页面

    def _on_tab_changed(self, index):
        """切换页面时停止普通手动控制，避免后台持续运动。"""
        if hasattr(self, "tabs") and index != 0:            # 离开手动页
            self.manual_hold_direction = (0.0, 0.0)        # 清除按键方向
            self.keys.clear()                              # 清除键盘状态
            if self.worker and self.connected:              # 已连接
                self._send(protocol.cmd_stop_all())         # 立即停车

    # ================= 串口连接 =================
    def _on_port_changed(self, port):
        """端口变化时自动切换推荐波特率。"""
        port = (port or "").strip().upper()                # 统一大写
        baud = config.PORT_BAUDRATE.get(port, config.SERIAL_BAUDRATE)   # 查推荐波特率
        self.baud_combo.setCurrentText(str(baud))          # 更新波特率

    def _refresh_ports(self):
        """刷新串口列表，优先保留当前选择。"""
        current = self.port_combo.currentText().strip() if hasattr(self, "port_combo") else ""   # 当前端口
        ports = [p.device for p in serial.tools.list_ports.comports()]   # 系统端口
        self.port_combo.blockSignals(True)                 # 暂停信号
        self.port_combo.clear()                            # 清空
        for port in ports:                                 # 添加实际端口
            self.port_combo.addItem(port)                  # 加入端口
        if current and current in ports:                   # 优先保留
            self.port_combo.setCurrentText(current)        # 恢复选择
        elif config.DEFAULT_PORT in ports:                 # 默认 COM7
            self.port_combo.setCurrentText(config.DEFAULT_PORT)   # 选择默认
        elif ports:                                        # 其它端口
            self.port_combo.setCurrentIndex(0)             # 选择第一个
        self.port_combo.blockSignals(False)                # 恢复信号
        if ports:                                          # 自动设置波特率
            self._on_port_changed(self.port_combo.currentText())   # 更新
        self._log("端口列表: " + (", ".join(ports) if ports else "未发现串口"))   # 记录

    def _toggle_connection(self):
        """连接或断开。"""
        if self.connected:                                 # 已连接
            self._disconnect()                             # 断开
        else:
            self._connect()                                # 连接

    def _connect(self):
        """创建串口线程或演示线程。"""
        if self.worker is not None:                        # 已有线程
            return                                         # 避免重复
        port = self.port_combo.currentText().strip()       # 端口
        baud = int(self.baud_combo.currentText())          # 波特率
        try:
            if self.chk_demo.isChecked():                  # 演示模式
                self.worker = DemoWorker()                 # 创建演示线程
            else:
                if not port:                               # 端口为空
                    self._log("未选择串口")                 # 提示
                    return                                 # 结束
                self.worker = SerialWorker(port, baud)     # 创建真实串口线程
            self._wire_worker()                            # 连接信号
            self.worker.start()                            # 启动线程
            mode = "演示模式" if self.chk_demo.isChecked() else port   # 连接对象
            self._log(f"正在连接 {mode}，{baud} bps")      # 日志
        except Exception as exc:                           # 创建失败
            self.worker = None                             # 清空
            self._log(f"连接创建失败: {exc}")               # 记录

    def _wire_worker(self):
        """连接线程信号。"""
        self.worker.connection_changed.connect(self._on_connection_changed)   # 连接状态
        self.worker.status_received.connect(self._on_status)                  # 状态
        self.worker.curve_received.connect(self._on_curve)                    # 曲线
        self.worker.ack_received.connect(self._on_ack)                        # ACK
        self.worker.params_received.connect(self._on_params)                  # 参数
        self.worker.log_received.connect(self._log)                           # 日志
        self.worker.tx_log.connect(lambda x: self._log(f"TX {x}"))            # 发送日志
        self.worker.rx_log.connect(lambda x: None)                            # 原始接收不刷屏
        if hasattr(self.worker, "rx_activity"):             # 演示线程可能没有
            self.worker.rx_activity.connect(self._on_rx_activity)             # 接收统计

    def _disconnect(self):
        """断开连接。"""
        if self.worker:                                     # 有线程
            self.worker.stop()                              # 请求停止
            self.worker.wait(1000)                          # 等待退出
            self.worker = None                              # 清空
        self.connected = False                              # 状态
        self.lbl_conn.setText("● 未连接")                    # 状态文字
        self.lbl_conn.setStyleSheet("color:#8A8F9E;")       # 灰色
        self.btn_connect.setText("连接")                     # 按钮文字
        self.lbl_mode.setText("--")                          # 模式
        self.statusBar().showMessage("未连接")               # 状态栏

    def _on_connection_changed(self, ok, msg):
        """连接状态回调。"""
        self.connected = ok                                 # 保存状态
        if ok:                                              # 已连接
            self.lbl_conn.setText(f"● {msg}")               # 文字
            self.lbl_conn.setStyleSheet("color:#00D1B2;")   # 绿色
            if hasattr(self, "lbl_dbg_link"):               # 调试页存在
                self.lbl_dbg_link.setText(f"● {msg}")       # 更新
            self.btn_connect.setText("断开")                 # 按钮
            self.statusBar().showMessage(msg)               # 状态栏
            self.last_rx_time = time.time()                 # 重置接收时间
            self.rx_bytes = 0                               # 重置接收计数
            self.lbl_rx.setText("0 bytes")                  # 显示
            self._send(protocol.cmd_heartbeat())            # 心跳
        else:                                               # 断开
            self.lbl_conn.setText(f"● {msg}")               # 文字
            self.lbl_conn.setStyleSheet("color:#FF5C6C;")   # 红色
            if hasattr(self, "lbl_dbg_link"):               # 调试页存在
                self.lbl_dbg_link.setText(f"● {msg}")       # 更新
            self.btn_connect.setText("连接")                 # 按钮
        self._log(msg)                                      # 日志

    # ================= 数据回调 =================
    def _on_status(self, data):
        """状态帧回调：更新状态和 PID 位置曲线。"""
        self.last_status = data                             # 保存状态
        if hasattr(self, "lbl_dbg_enc"):                    # 调试页存在
            self.lbl_dbg_enc.setText("计数: " + " / ".join(str(v) for v in data.get("enc", [])))   # 更新计数
        names = {0: "空闲", 1: "手动", 3: "PID停", 4: "路线", 5: "旋转"}   # 模式名称
        self.mode_name = names.get(data.get("mode", 0), "未知")   # 当前模式
        self.lbl_mode.setText(self.mode_name)               # 更新模式
        self.lbl_batt.setText(f"{data.get('battery', 0)} mV")   # 电池
        self.lbl_speed.setText(" / ".join(f"{v:.2f}" for v in data.get("speed", [])))   # 速度
        self.lbl_enc.setText(" / ".join(str(v) for v in data.get("enc", [])))            # 编码器

        if self.pid_active and self.pid_start_counts is not None:   # PID 运行中
            enc = data.get("enc", [])                       # 当前计数
            if len(enc) >= 4:                               # 数据完整
                deltas = [enc[i] - self.pid_start_counts[i] for i in range(4)]   # 相对起点计数
                avg_counts = sum(deltas) / 4.0             # 四轮平均计数
                actual_m = self._counts_to_distance(avg_counts)   # 实际距离 m
                actual_mm = actual_m * 1000.0              # mm
                target_mm = self.pid_target_m * 1000.0     # 目标 mm
                error_mm = target_mm - actual_mm            # 误差 mm
                self.pid_actual_m = actual_m                # 保存实际位置
                self.pid_error_mm = error_mm                # 保存误差
                if hasattr(self, "lbl_pid_actual"):         # 控制页存在
                    self.lbl_pid_actual.setText(f"{actual_mm:.1f} mm")   # 实际位置
                    self.lbl_pid_error.setText(f"{error_mm:+.1f} mm")    # 误差
                if hasattr(self, "curve_panel"):            # 主曲线页也显示位置
                    self.curve_panel.update_position(target_mm, actual_mm, error_mm)   # 更新主曲线位置
                if hasattr(self, "pid_curve_panel"):        # 控制页曲线
                    self.pid_curve_panel.update_position(target_mm, actual_mm, error_mm)   # 更新位置曲线
                if abs(error_mm) <= config.POS_STOP_TOL_MM: # 进入容差
                    if hasattr(self, "lbl_pid_state"):      # 状态标签
                        self.lbl_pid_state.setText(f"已进入容差 (±{config.POS_STOP_TOL_MM:.0f} mm)")   # 提示

    def _on_curve(self, data):
        """曲线帧回调：四轮目标/实际速度。"""
        target = data.get("target", [0, 0, 0, 0])           # 目标速度
        actual = data.get("actual", [0, 0, 0, 0])           # 实际速度
        if hasattr(self, "curve_panel"):                    # 主曲线页
            self.curve_panel.update_data(target, actual)    # 更新
        if hasattr(self, "pid_curve_panel"):                # 控制页曲线
            self.pid_curve_panel.update_data(target, actual)   # 更新

    def _on_ack(self, data):
        """ACK 回调。"""
        self._log(f"ACK cmd=0x{data.get('cmd', 0):02X} err={data.get('err', 0)}")   # 日志
        if self.link_test_pending and data.get("cmd") == config.CMD_HEARTBEAT:   # 心跳测试
            self.link_test_pending = False                  # 清除等待
            self._log("链路测试成功：收到心跳 ACK")           # 提示

    def _on_params(self, data):
        """参数帧回调。"""
        if hasattr(self, "spin_kp"):                        # 控制页存在
            self.spin_kp.setValue(data.get("kp", 0.0))       # Kp
            self.spin_ki.setValue(data.get("ki", 0.0))       # Ki
            self.spin_kd.setValue(data.get("kd", 0.0))       # Kd
        if hasattr(self, "param_kp"):                       # 参数页存在
            self.param_kp.setValue(data.get("kp", 0.0))      # Kp
            self.param_ki.setValue(data.get("ki", 0.0))      # Ki
            self.param_kd.setValue(data.get("kd", 0.0))      # Kd
            self.param_vmax.setValue(data.get("vmax", config.MAX_VX))   # vmax
            self.param_wmax.setValue(data.get("wmax", config.MAX_WZ))   # wmax
        self._log("参数已读取")                            # 日志

    def _on_rx_activity(self, n):
        """更新接收统计和链路状态。"""
        self.last_rx_time = time.time()                     # 接收时间
        self.rx_bytes += n                                  # 累计字节
        self.lbl_rx.setText(f"{self.rx_bytes} bytes")       # 显示
        if hasattr(self, "lbl_dbg_rx"):                     # 调试页存在
            self.lbl_dbg_rx.setText(f"RX: {self.rx_bytes} bytes")   # 更新
        if hasattr(self, "lbl_dbg_link"):                   # 调试页存在
            self.lbl_dbg_link.setText("● 已连接（数据正常）")   # 更新
        if self.connected:                                  # 已连接
            self.lbl_conn.setText("● 已连接（数据正常）")    # 更新
            self.lbl_conn.setStyleSheet("color:#00D1B2;")   # 绿色

    def _update_link_status(self):
        """每秒检查是否还有数据。"""
        if not self.connected:                              # 未连接
            return                                          # 跳过
        if time.time() - self.last_rx_time > 1.5:           # 1.5s 没有数据
            self.lbl_conn.setText("● 已连接（无数据）")      # 黄色提示
            self.lbl_conn.setStyleSheet("color:#FFC857;")   # 黄色
            if hasattr(self, "lbl_dbg_link"):               # 调试页存在
                self.lbl_dbg_link.setText("● 已连接（无数据）")   # 更新
        else:                                               # 数据正常
            self.lbl_conn.setText("● 已连接（数据正常）")    # 绿色
            self.lbl_conn.setStyleSheet("color:#00D1B2;")   # 绿色

    def _link_test(self):
        """发送心跳并等待 ACK。"""
        if not (self.worker and self.connected):            # 未连接
            self._log("请先连接")                            # 提示
            return                                          # 结束
        self.link_test_pending = True                       # 标记等待
        self._send(protocol.cmd_heartbeat())                # 发心跳
        self._log("已发送心跳，等待 ACK...")                 # 提示
        QTimer.singleShot(1500, self._link_test_timeout)   # 超时检查

    def _link_test_timeout(self):
        """链路测试超时。"""
        if self.link_test_pending:                          # 仍在等待
            self.link_test_pending = False                  # 清除标记
            self._log("链路测试失败：1.5 秒内未收到 ACK（检查接线/波特率/AT 模式）")   # 提示

    # ================= 手动控制 =================
    def _manual_button_pressed(self, dx, dy):
        """方向按钮按下：记录方向并立即发送。"""
        speed = self.sl_speed.value() / 100.0               # 当前速度
        self.manual_hold_direction = (dx * speed, dy * speed)   # 记录方向
        self.manual_pause_until = 0.0                       # 清除暂停
        self._send(protocol.cmd_manual(dx * speed, dy * speed, 0.0))   # 立即发送

    def _manual_button_released(self):
        """方向按钮松开：立即停车。"""
        self.manual_hold_direction = (0.0, 0.0)             # 清方向
        self._send(protocol.cmd_stop_all())                  # 立即停车

    def _manual_stop(self):
        """停止手动控制。"""
        self.manual_hold_direction = (0.0, 0.0)             # 清方向
        self.keys.clear()                                   # 清键盘
        self._send(protocol.cmd_stop_all())                  # 全停
        self._log("手动控制已停止")                         # 日志

    def _manual_tick(self):
        """周期发送手动速度；只在手动页且按住时发送。"""
        if not self.connected or self.worker is None:       # 未连接
            return                                          # 结束
        if self.tabs.currentIndex() != 0:                   # 不在手动页
            return                                          # 结束
        if self.route_active or time.time() < self.manual_pause_until:   # 路线/特殊动作中
            return                                          # 结束
        speed = self.sl_speed.value() / 100.0               # 共用平移速度
        vx, vy = self.manual_hold_direction                 # 按钮方向
        if "W" in self.keys: vx += speed                    # 键盘前进
        if "S" in self.keys: vx -= speed                    # 键盘后退
        if "A" in self.keys: vy += speed                    # 键盘左移
        if "D" in self.keys: vy -= speed                    # 键盘右移
        if abs(vx) < 1e-6 and abs(vy) < 1e-6:               # 没有输入
            return                                          # 不周期刷停车帧
        vx = max(-1.0, min(1.0, vx))                        # 限幅
        vy = max(-1.0, min(1.0, vy))                        # 限幅
        self._send(protocol.cmd_manual(vx, vy, 0.0))        # 直接速度，不使用 PID

    def _rotate_by_angle(self, direction):
        """按键转设定角度：direction=+1 左转，-1 右转。"""
        self._rotate_angle(direction * self.spin_rot_angle.value())   # 读取角度

    def _rotate_angle(self, deg):
        """原地旋转指定角度；时间控制，不使用 PID。"""
        if not (self.worker and self.connected):            # 未连接
            self._log("请先连接")                            # 提示
            return                                          # 结束
        self.manual_hold_direction = (0.0, 0.0)             # 清方向
        self.keys.clear()                                   # 清键盘
        self._send(protocol.cmd_stop_all())                 # 先停
        duration = abs(deg) / 90.0 * config.ROTATE_MS_PER_90 / 1000.0 + 0.4   # 预计旋转时间
        self.manual_pause_until = time.time() + duration    # 暂停手动发送
        self._send(protocol.cmd_rotate(deg))                # 发送旋转
        self._log(f"原地旋转 {deg:+.1f}°（时间控制，不使用 PID）")   # 日志

    # ================= 调试/标定 =================
    def _send_raw_frame(self):
        """发送输入的十六进制原始帧。"""
        text = self.edit_raw.text().replace(" ", "").replace(",", "")   # 清理输入
        try:
            data = bytes.fromhex(text)                      # 转字节
        except ValueError:
            self._log("原始帧格式错误，请输入十六进制，如 AA 55 01 0A 0B")   # 提示
            return                                          # 结束
        if not (self.worker and self.connected):            # 未连接
            self._log("请先连接")                            # 提示
            return                                          # 结束
        self.worker.send_frame(data)                         # 发送
        self._log(f"原始帧已发送: {data.hex(' ').upper()}")  # 日志

    def _calib_record_start(self):
        """记录编码器标定起点。"""
        if not self.last_status:                             # 没有状态帧
            self._log("还没有收到编码器数据，先连接并等待状态帧")   # 提示
            return                                          # 结束
        self.calib_start_counts = list(self.last_status["enc"])   # 保存起点
        self._log(f"编码器起点: {self.calib_start_counts}")  # 日志

    def _calib_compute_cpr(self):
        """根据实际距离计算建议 CPR。"""
        if not self.calib_start_counts or not self.last_status:   # 缺数据
            self._log("请先记录起点，并确认已收到终点状态帧")   # 提示
            return                                          # 结束
        end = self.last_status["enc"]                       # 终点计数
        deltas = [end[i] - self.calib_start_counts[i] for i in range(4)]   # 四轮差
        avg = sum(deltas) / 4.0                             # 平均计数
        dist_m = self.spin_calib_mm.value() / 1000.0        # 实际距离
        circumference = math.pi * (config.WHEEL_DIAMETER_MM / 1000.0)   # 轮周长
        if dist_m <= 0.001:                                 # 距离太小
            self._log("实际距离太小，无法计算")             # 提示
            return                                          # 结束
        rev = dist_m / circumference                        # 输出轴圈数
        suggested = abs(avg) / rev if rev > 0 else 0.0      # 建议 CPR
        self.lbl_calib_result.setText(f"建议 CPR: {suggested:.0f} counts/rev")   # 显示
        self._log(f"CPR 标定: 平均计数={avg:.1f}, 距离={dist_m:.3f}m, 建议 CPR={suggested:.0f}")   # 日志

    def _rotate_calib_send(self):
        """发送一次 90° 旋转供标定。"""
        self._send(protocol.cmd_rotate(90))                 # 发送 90°
        self._log("已发送左转 90°，请测量实际角度后填写")   # 提示

    def _rotate_calib_compute(self):
        """根据实测角度计算建议 90° 时间。"""
        measured = self.spin_calib_deg.value()              # 实测角度
        if measured <= 0.1:                                 # 角度太小
            self._log("实测角度必须大于 0")                 # 提示
            return                                          # 结束
        suggested = config.ROTATE_MS_PER_90 * 90.0 / measured   # 建议时间
        self.lbl_rot_result.setText(f"建议 90° 时间: {suggested:.0f} ms")   # 显示
        self._log(f"旋转标定: 实测 {measured:.1f}°，建议 90° 时间 {suggested:.0f} ms")   # 日志

    def _pulse_motion(self, vx, vy, wz, ms=600):
        """短脉冲运动：发一段速度，到时自动停。"""
        if not (self.worker and self.connected):            # 未连接
            self._log("请先连接")                            # 提示
            return                                          # 结束
        self.manual_pause_until = time.time() + (ms / 1000.0) + 0.2   # 防止手动覆盖
        self._send(protocol.cmd_manual(vx, vy, wz))          # 发送速度
        QTimer.singleShot(ms, lambda: self._send(protocol.cmd_stop_all()))   # 到时停
        self._log(f"点动: vx={vx} vy={vy} wz={wz}，{ms}ms")  # 日志

    def _geo_compute(self):
        """本地预览麦轮逆运动学的四轮速度。"""
        vx = self.spin_geo_vx.value()                       # vx
        vy = self.spin_geo_vy.value()                       # vy
        wz = self.spin_geo_wz.value()                       # wz
        a = config.WHEELBASE_MM / 2000.0                    # 半轴距
        b = config.TRACK_MM / 2000.0                        # 半轮距
        lw = a + b                                          # 几何参数
        w = [vx - vy - lw * wz,                             # A
             vx + vy + lw * wz,                             # B
             vx + vy - lw * wz,                             # C
             vx - vy + lw * wz]                             # D
        self.lbl_geo.setText("A/B/C/D: " + " / ".join(f"{x:.3f}" for x in w) + " m/s")   # 显示
        self._log(f"几何预览: {self.lbl_geo.text()}")        # 日志

    # ================= PID 控制与参数 =================
    def _counts_to_distance(self, counts):
        """编码器计数换算距离（m）。"""
        rev = counts / config.ENCODER_CPR                   # 输出轴圈数
        return rev * math.pi * (config.WHEEL_DIAMETER_MM / 1000.0)   # 距离

    def _on_pid_apply(self):
        """下发 PID 参数。"""
        if not (self.worker and self.connected):            # 未连接
            self._log("请先连接")                            # 提示
            return                                          # 结束
        self._send(protocol.cmd_set_pos_pid(self.spin_kp.value(),
                                            self.spin_ki.value(),
                                            self.spin_kd.value()))   # 单发 PID
        self._log("位置 PID 参数已下发（只在控制与测试页使用）")   # 日志

    def _on_pid_read(self):
        """读取当前 PID 参数。"""
        self._send(protocol.cmd_read_params())              # 读取
        self._log("已请求读取 PID 参数")                    # 日志

    def _on_pid_start(self):
        """开始 PID 位置控制。"""
        if not (self.worker and self.connected):            # 未连接
            self._log("请先连接")                            # 提示
            return                                          # 结束
        if not self.last_status:                             # 尚未收到状态
            self._log("还没有编码器状态，等待状态帧后再开始")   # 提示
            return                                          # 结束
        if self.route_active:                               # 路线运行中
            self._log("请先停止固定路线")                   # 提示
            return                                          # 结束
        self.pid_start_counts = list(self.last_status["enc"])   # 记录起点
        self.pid_target_m = self.spin_pid_mm.value() / 1000.0   # 目标距离
        self.pid_actual_m = 0.0                             # 初始实际
        self.pid_error_mm = self.pid_target_m * 1000.0      # 初始误差
        self.pid_started_at = time.time()                   # 开始时间
        self.pid_active = True                              # 标记运行
        if hasattr(self, "pid_curve_panel"):                # 清曲线
            self.pid_curve_panel.clear()                    # 清空
        if hasattr(self, "lbl_pid_target"):                 # 更新目标
            self.lbl_pid_target.setText(f"{self.spin_pid_mm.value()} mm")   # 目标
            self.lbl_pid_actual.setText("0.0 mm")           # 实际
            self.lbl_pid_error.setText(f"{self.pid_error_mm:+.1f} mm")   # 误差
            self.lbl_pid_state.setText("运行中")             # 状态
        self._send(protocol.cmd_set_pos_pid(self.spin_kp.value(),
                                            self.spin_ki.value(),
                                            self.spin_kd.value()))   # 先下发参数
        self._send(protocol.cmd_pid_stop(self.spin_pid_mm.value()))   # 开始位置控制
        self._log(f"PID 位置控制开始：目标 {self.spin_pid_mm.value()} mm")   # 日志

    def _on_pid_abort(self):
        """停止 PID 控制。"""
        self.pid_active = False                             # 清除运行
        self._send(protocol.cmd_stop_all())                 # 全停
        if hasattr(self, "lbl_pid_state"):                  # 状态标签
            self.lbl_pid_state.setText("已停止")             # 更新
        self._log("PID 位置控制已停止")                     # 日志

    def _on_pid_stop(self):
        """兼容旧按钮：停止 PID。"""
        self._on_pid_abort()                                # 调用停止

    def _param_apply(self):
        """参数页：下发运行期参数。"""
        if not (self.worker and self.connected):            # 未连接
            self._log("请先连接")                            # 提示
            return                                          # 结束
        self._send(protocol.cmd_set_pos_pid(self.param_kp.value(),
                                            self.param_ki.value(),
                                            self.param_kd.value()))   # PID
        self._send(protocol.cmd_set_limits(self.param_vmax.value(),
                                           self.param_wmax.value()))  # 限幅
        if hasattr(self, "spin_kp"):                        # 同步控制页
            self.spin_kp.setValue(self.param_kp.value())    # Kp
            self.spin_ki.setValue(self.param_ki.value())    # Ki
            self.spin_kd.setValue(self.param_kd.value())    # Kd
        self._log("运行期参数已下发")                       # 日志

    def _param_read(self):
        """参数页：读取当前参数。"""
        self._send(protocol.cmd_read_params())              # 读取
        self._log("已请求读取运行期参数")                   # 日志

    def _send(self, frame):
        """发送一帧。"""
        if self.worker and self.connected:                  # 已连接
            self.worker.send_frame(frame)                   # 发送

    # ================= 键盘 =================
    def keyPressEvent(self, event):
        """键盘按下：WASD 移动，Q/E 按设定角度旋转，空格急停。"""
        if event.isAutoRepeat():                            # 忽略系统重复
            return
        key = event.key()                                   # 键码
        if key == Qt.Key_Space:                             # 空格急停
            self._manual_stop()                             # 急停
            return                                          # 结束
        text = event.text().upper()                         # 文本
        if text in ("W", "A", "S", "D"):                    # 移动键
            self.keys.add(text)                             # 记录
        elif text == "Q":                                   # 左转
            self._rotate_by_angle(1.0)                      # 左转
        elif text == "E":                                   # 右转
            self._rotate_by_angle(-1.0)                     # 右转
        super().keyPressEvent(event)                        # 父类处理

    def keyReleaseEvent(self, event):
        """键盘松开：WASD 松开立即停。"""
        if event.isAutoRepeat():                            # 忽略系统重复
            return
        text = event.text().upper()                         # 文本
        if text in ("W", "A", "S", "D"):                    # 移动键
            self.keys.discard(text)                         # 移除
            if not self.keys and self.manual_hold_direction == (0.0, 0.0):   # 没有其它输入
                self._send(protocol.cmd_stop_all())         # 立即停
        super().keyReleaseEvent(event)                      # 父类处理

    # ================= 日志/关闭 =================
    def _log(self, text):
        """追加日志。"""
        if not hasattr(self, "log_view"):                   # 日志页尚未创建
            return                                          # 跳过
        now = datetime.datetime.now().strftime("%H:%M:%S") # 时间
        self.log_view.appendPlainText(f"[{now}] {text}")    # 追加
        self.statusBar().showMessage(str(text), 3000)       # 状态栏提示

    def closeEvent(self, event):
        """关闭窗口时断开连接。"""
        self._disconnect()                                  # 断开
        event.accept()                                      # 接受关闭
