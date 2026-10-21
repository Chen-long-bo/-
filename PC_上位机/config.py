# -*- coding: utf-8 -*-
"""上位机全局配置：所有可调参数集中在这里。"""

# ===== 程序信息 =====
APP_NAME = "麦轮小车控制台"          # 窗口标题
WINDOW_W = 1280                     # 默认窗口宽度
WINDOW_H = 820                      # 默认窗口高度

# ===== 串口 =====
SERIAL_BAUDRATE = 9600              # 默认波特率（HC-04 SPP）
BAUDRATE_OPTIONS = [9600, 115200]   # 可选波特率（COM5有线调试用115200）
PORT_BAUDRATE = {"COM5": 115200}    # 指定端口的默认波特率
SERIAL_TIMEOUT = 0.05               # 串口读超时（秒）
DEFAULT_PORT = "COM7"               # 当前 HC-04 的“传出”口（SPP 客户端）
PORT_CANDIDATES = ["COM7", "COM4", "COM5"]   # 候选端口（COM7=蓝牙传出，COM4=蓝牙传入）
TX_INTERVAL_MS = 50                 # 手动控制发送周期（毫秒）

# ===== 车体尺寸（已量） =====
WHEEL_DIAMETER_MM = 80.0            # 轮径 mm
WHEELBASE_MM = 130.0                # 前后轴距 mm
TRACK_MM = 123.5                    # 左右轮中心距 mm
ENCODER_CPR = 2464.0                # 4倍频每转计数

# ===== 运动限幅（默认值，可在界面调整） =====
MAX_VX = 1.00                       # 最大前后速度 m/s（摇杆拉满=1.0）
MAX_VY = 1.00                       # 最大左右速度 m/s（摇杆拉满=1.0）
MAX_WZ = 1.50                       # 最大旋转角速度 rad/s
MIN_DRIVE = 0.30                     # 固件最小有效驱动（归一化，仅显示/标定参考）
ROTATE_DRIVE = 0.60                  # 固件原地旋转轮速（归一化，仅显示）
ROTATE_MS_PER_90 = 900               # 固件转90°默认时间 ms（用于旋转标定）
POS_STOP_TOL_MM = 10.0               # 固件位置停容差 mm（仅显示）

# ===== 协议指令码 =====
CMD_MANUAL = 0x01                   # 手动全向速度
CMD_BRAKE_FAST = 0x02               # 急刹停
CMD_PID_STOP = 0x04                 # PID精准停
CMD_ROUTE = 0x05                    # 固定路线
CMD_STOP_ALL = 0x06                 # 急停
CMD_SET_SPEED_PID = 0x07            # 预留（速度环在模块内部）
CMD_SET_POS_PID = 0x08              # 设置位置环PID
CMD_ENC_ZERO = 0x09                 # 编码器清零
CMD_HEARTBEAT = 0x0A                # 心跳
CMD_READ_PARAMS = 0x0B              # 读取参数
CMD_SET_LIMITS = 0x0C               # 设置限幅
CMD_ROTATE_ANGLE = 0x0D             # 原地旋转指定角度（0.1度）

# ===== 协议回报码 =====
RPT_STATUS = 0x81                   # 状态帧
RPT_CURVE = 0x82                    # 曲线帧
RPT_ACK = 0x83                      # ACK
RPT_LOG = 0x84                      # 日志
RPT_PARAMS = 0x85                   # 参数帧

# ===== 颜色（优雅黑风格） =====
COLOR_BG = "#0E0F13"                # 窗口背景
COLOR_PANEL = "#15161C"             # 面板背景
COLOR_PANEL_2 = "#1B1D25"           # 次级面板
COLOR_BORDER = "#2A2D38"            # 边框
COLOR_TEXT = "#E6E8EF"              # 主文字
COLOR_SUBTEXT = "#8A8F9E"           # 次文字
COLOR_ACCENT = "#00D1B2"            # 主强调色（青绿）
COLOR_BLUE = "#4F8CFF"              # 次强调色（蓝）
COLOR_RED = "#FF5C6C"               # 危险/急停
COLOR_YELLOW = "#FFC857"            # 警告

# ===== 曲线颜色（A/B/C/D 四轮） =====
WHEEL_COLORS = ["#00D1B2", "#4F8CFF", "#FFC857", "#FF5C6C"]

# ===== 控制与测试页默认值 =====
DEFAULT_POS_KP = 0.80               # 位置环Kp
DEFAULT_POS_KI = 0.00               # 位置环Ki
DEFAULT_POS_KD = 0.00               # 位置环Kd
DEFAULT_ROUTE_SIDE_MM = 800         # 正方形边长 mm

# ===== 曲线缓存点数 =====
CURVE_MAX_POINTS = 400              # 曲线保留点数








