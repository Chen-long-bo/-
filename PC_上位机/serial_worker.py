# -*- coding: utf-8 -*-
"""串口线程：负责打开串口、收发数据、解析协议帧。"""

import time                                     # 时间
import threading                                # 线程锁
import serial                                   # pyserial
from PySide6.QtCore import QThread, Signal      # Qt线程与信号
import config                                   # 全局配置
import protocol                                 # 协议模块


class SerialWorker(QThread):
    """串口工作线程。"""

    connection_changed = Signal(bool, str)      # 连接状态变化（是否连接, 说明）
    status_received = Signal(dict)              # 收到状态帧
    curve_received = Signal(dict)               # 收到曲线帧
    ack_received = Signal(dict)                 # 收到ACK
    params_received = Signal(dict)              # 收到参数帧
    log_received = Signal(str)                  # 日志
    tx_log = Signal(str)                        # 发送日志
    rx_log = Signal(str)                        # 接收日志
    rx_activity = Signal(int)                   # 收到数据的活动信号（字节数）

    def __init__(self, port: str, baudrate: int = 9600):
        super().__init__()                      # 初始化父类
        self.port = port                        # 端口名
        self.baudrate = baudrate                # 波特率
        self._serial = None                     # 串口对象
        self._running = False                   # 运行标志
        self._lock = threading.Lock()           # 写锁

    def run(self):
        """线程主循环：打开串口并持续读取。"""
        try:
            self._serial = serial.Serial(       # 打开串口
                self.port,                      # 端口
                self.baudrate,                  # 波特率
                timeout=config.SERIAL_TIMEOUT,  # 读超时
            )
            self._serial.reset_input_buffer()   # 清空输入缓冲
            self._running = True                # 标记运行
            self.connection_changed.emit(True, f"已连接 {self.port}")   # 通知界面
            parser = protocol.FrameParser()     # 创建帧解析器
            while self._running:                # 主循环
                data = self._serial.read(256)   # 读取数据
                if data:                        # 有数据
                    self.rx_log.emit(data.hex(" ").upper())   # 记录原始数据
                    self.rx_activity.emit(len(data))           # 通知界面收到数据
                    for b in data:              # 逐字节喂给解析器
                        for cmd, payload in parser.feed(b):
                            self._dispatch(cmd, payload)   # 分发解析结果
                time.sleep(0.001)               # 稍微让出CPU
        except Exception as e:                  # 捕获异常
            self.connection_changed.emit(False, f"串口错误: {e}")   # 通知界面
        finally:
            if self._serial and self._serial.is_open:   # 如果串口还开着
                self._serial.close()            # 关闭串口
            self._serial = None                 # 清空对象
            self._running = False               # 标记停止

    def _dispatch(self, cmd: int, payload: bytes):
        """根据回报码分发解析结果。"""
        if cmd == config.RPT_STATUS:            # 状态帧
            r = protocol.parse_status(payload)  # 解析
            if r: self.status_received.emit(r)  # 发出
        elif cmd == config.RPT_CURVE:           # 曲线帧
            r = protocol.parse_curve(payload)   # 解析
            if r: self.curve_received.emit(r)   # 发出
        elif cmd == config.RPT_ACK:             # ACK
            r = protocol.parse_ack(payload)     # 解析
            if r: self.ack_received.emit(r)     # 发出
        elif cmd == config.RPT_PARAMS:          # 参数帧
            r = protocol.parse_params(payload)  # 解析
            if r: self.params_received.emit(r)  # 发出
        elif cmd == config.RPT_LOG:             # 日志帧
            self.log_received.emit(payload.decode("utf-8", "replace"))   # 解码日志

    def send_frame(self, frame: bytes):
        """发送一帧数据。"""
        with self._lock:                        # 加锁
            if self._serial and self._serial.is_open:   # 串口可用
                try:
                    self._serial.write(frame)   # 写入
                    self._serial.flush()        # 立即发送
                    self.tx_log.emit(frame.hex(" ").upper())   # 记录
                except Exception as e:          # 写入异常
                    self.log_received.emit(f"发送失败: {e}")   # 记录

    def stop(self):
        """请求停止线程。"""
        self._running = False                   # 清除运行标志


