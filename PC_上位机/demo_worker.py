# -*- coding: utf-8 -*-
"""演示模式：没有硬件时模拟小车，方便开发和看界面。"""

import math                                     # 数学函数
import struct                                   # 解析指令数据
from PySide6.QtCore import QThread, Signal      # Qt线程与信号
import config                                   # 全局配置
import protocol                                 # 协议模块


class DemoWorker(QThread):
    """模拟小车线程，接口与 SerialWorker 一致。"""

    connection_changed = Signal(bool, str)      # 连接状态
    status_received = Signal(dict)              # 状态帧
    curve_received = Signal(dict)               # 曲线帧
    ack_received = Signal(dict)                 # ACK
    params_received = Signal(dict)              # 参数帧
    log_received = Signal(str)                  # 日志
    tx_log = Signal(str)                        # 发送日志
    rx_log = Signal(str)                        # 接收日志

    def __init__(self):
        super().__init__()                      # 父类初始化
        self._running = False                   # 运行标志
        self.mode = 0                           # 模式
        self.target = [0.0, 0.0]                # 目标vx/vy
        self.target_wz = 0.0                    # 目标wz
        self.actual = [0.0, 0.0, 0.0, 0.0]      # 四轮实际线速度
        self.enc = [0, 0, 0, 0]                 # 四轮累计计数
        self.target_wheel = [0.0, 0.0, 0.0, 0.0] # 四轮目标线速度
        self.kp, self.ki, self.kd = config.DEFAULT_POS_KP, config.DEFAULT_POS_KI, config.DEFAULT_POS_KD  # PID
        self.vmax, self.wmax = config.MAX_VX, config.MAX_WZ   # 限幅
        self.pos_target = 0.0                   # 位置停目标
        self.pos_start = 0.0                    # 位置停起点
        self.distance = 0.0                     # 当前距离
        self.soft_stop = False                  # 缓停标志

    def start(self):
        """启动模拟线程。"""
        self._running = True                    # 置运行标志
        super().start()                         # 启动线程

    def run(self):
        """线程主循环：每50ms更新一次。"""
        self.connection_changed.emit(True, "演示模式")   # 通知界面
        dt = 0.05                               # 周期50ms
        while self._running:                    # 循环
            self._update(dt)                    # 更新状态
            self._emit_reports()                # 上报
            self.msleep(50)                     # 休眠50ms
        self.connection_changed.emit(False, "演示已停止")   # 通知结束

    def _update(self, dt: float):
        """更新模拟状态。"""
        if self.mode == 1:                      # 手动
            vx, vy = self.target                # 取目标
            wz = self.target_wz                 # 取角速度
        elif self.mode == 3:                    # PID精准停
            err = self.pos_target + self.pos_start - self.distance   # 位置误差
            vx = max(-self.vmax, min(self.vmax, err * self.kp))      # P控制
            vy, wz = 0.0, 0.0                   # 只前后
            if abs(err) < 0.01:                 # 到位
                self.mode = 0                   # 停止
                vx = 0.0                        # 速度0
        elif self.mode == 2:                    # 缓停
            vx, vy, wz = self.target[0], self.target[1], self.target_wz   # 当前目标
            vx *= 0.85                          # 逐步减小
            vy *= 0.85                          # 逐步减小
            wz *= 0.85                          # 逐步减小
            self.target = [vx, vy]              # 保存
            self.target_wz = wz                 # 保存
            if abs(vx) < 0.002 and abs(vy) < 0.002 and abs(wz) < 0.002:  # 足够小
                self.mode = 0                   # 停止
        else:
            vx, vy, wz = 0.0, 0.0, 0.0          # 其它模式停止

        a = (config.WHEELBASE_MM / 2000.0)      # 半轴距 m
        b = (config.TRACK_MM / 2000.0)          # 半轮距 m
        lw = a + b                              # 麦轮几何参数
        self.target_wheel[0] = vx - vy - lw * wz   # 左前
        self.target_wheel[1] = vx + vy + lw * wz   # 右前
        self.target_wheel[2] = vx + vy - lw * wz   # 左后
        self.target_wheel[3] = vx - vy + lw * wz   # 右后

        for i in range(4):                      # 四轮一阶跟随
            diff = self.target_wheel[i] - self.actual[i]   # 误差
            self.actual[i] += diff * 0.35       # 跟随
            if abs(self.actual[i]) < 0.001:     # 很小则归零
                self.actual[i] = 0.0
            rev = self.actual[i] * dt / (math.pi * config.WHEEL_DIAMETER_MM / 1000.0)   # 转数
            self.enc[i] += int(rev * config.ENCODER_CPR)   # 累加计数

        self.distance += (self.actual[0] + self.actual[1] + self.actual[2] + self.actual[3]) / 4.0 * dt   # 平均距离

    def _emit_reports(self):
        """发出状态帧和曲线帧。"""
        status = {"mode": self.mode, "battery": 12300,
                  "enc": list(self.enc), "speed": list(self.actual)}   # 状态
        self.status_received.emit(status)       # 发出状态
        curve = {"target": list(self.target_wheel), "actual": list(self.actual)}   # 曲线
        self.curve_received.emit(curve)         # 发出曲线

    def send_frame(self, frame: bytes):
        """接收界面指令并更新模拟状态。"""
        self.tx_log.emit(frame.hex(" ").upper())   # 记录发送
        parser = protocol.FrameParser()         # 临时解析器
        for b in frame:                         # 逐字节
            for cmd, data in parser.feed(b):    # 解析
                self._handle(cmd, data)         # 处理

    def _handle(self, cmd: int, data: bytes):
        """处理一条指令。"""
        if cmd == config.CMD_MANUAL and len(data) >= 6:   # 手动
            vx, vy, wz = struct.unpack_from("<hhh", data, 0)   # 解析
            self.target = [vx / 1000.0, vy / 1000.0]           # 保存
            self.target_wz = wz / 1000.0                       # 保存
            self.mode = 1                                      # 手动模式
        elif cmd == config.CMD_BRAKE_FAST:      # 急刹
            self.target = [0.0, 0.0]            # 目标清零
            self.target_wz = 0.0                # 角速度清零
            self.actual = [0.0, 0.0, 0.0, 0.0]  # 立即停
            self.mode = 0                       # 空闲
        elif cmd == config.CMD_BRAKE_SOFT:      # 缓停
            self.mode = 2                       # 缓停模式
        elif cmd == config.CMD_PID_STOP and len(data) >= 2:   # 位置停
            target_mm = struct.unpack_from("<h", data, 0)[0]  # 目标mm
            self.pos_start = self.distance      # 起点
            self.pos_target = target_mm / 1000.0   # 目标m
            self.mode = 3                       # 位置停模式
        elif cmd == config.CMD_ROUTE:           # 路线（演示简化为前进）
            self.target = [0.25, 0.0]           # 前进
            self.target_wz = 0.0                # 不转
            self.mode = 1                       # 手动模式
        elif cmd == config.CMD_STOP_ALL:        # 急停
            self.target = [0.0, 0.0]            # 清零
            self.target_wz = 0.0                # 清零
            self.actual = [0.0, 0.0, 0.0, 0.0]  # 停
            self.mode = 0                       # 空闲
        elif cmd == config.CMD_SET_POS_PID and len(data) >= 6:   # 设置PID
            kp, ki, kd = struct.unpack_from("<HHH", data, 0)     # 解析
            self.kp, self.ki, self.kd = kp / 1000.0, ki / 1000.0, kd / 1000.0   # 保存
            ack = {"cmd": cmd, "err": 0}        # ACK
            self.ack_received.emit(ack)         # 发出
        elif cmd == config.CMD_ENC_ZERO:        # 编码器清零
            self.enc = [0, 0, 0, 0]             # 清零
        elif cmd == config.CMD_HEARTBEAT:       # 心跳
            self.ack_received.emit({"cmd": cmd, "err": 0})   # 回复
        elif cmd == config.CMD_READ_PARAMS:     # 读参数
            self.params_received.emit({         # 返回参数
                "kp": self.kp, "ki": self.ki, "kd": self.kd,
                "vmax": self.vmax, "wmax": self.wmax})
        elif cmd == config.CMD_SET_LIMITS and len(data) >= 4:    # 设置限幅
            vmax, wmax = struct.unpack_from("<HH", data, 0)      # 解析
            self.vmax, self.wmax = vmax / 1000.0, wmax / 1000.0  # 保存
        self.log_received.emit(f"演示收到指令 0x{cmd:02X}")       # 日志

    def stop(self):
        """停止模拟线程。"""
        self._running = False                   # 清除运行标志
