# -*- coding: utf-8 -*-
"""通信协议：帧打包、帧解析、指令构造、回报解析。"""

import struct                                   # 使用struct做小端打包
import config                                   # 导入全局配置


def checksum(payload: bytes) -> int:
    """计算校验和：所有字节相加取低8位。"""
    return sum(payload) & 0xFF                   # 求和后取低8位


def build_frame(cmd: int, data: bytes = b"") -> bytes:
    """构造一帧：AA 55 LEN CMD DATA CHECK。"""
    length = 1 + len(data)                       # LEN = CMD + DATA 的字节数
    payload = bytes([length, cmd]) + data        # 参与校验的部分
    return bytes([0xAA, 0x55]) + payload + bytes([checksum(payload)])   # 完整帧


class FrameParser:
    """逐字节状态机：从串口数据流中提取完整帧。"""

    def __init__(self):
        self.buf = bytearray()                   # 当前帧数据缓存
        self.need = 0                            # 还需要读取的字节数（CMD+DATA）
        self.length = 0                          # 当前帧的LEN字段
        self.state = "sof1"                      # 当前状态

    def feed(self, byte: int):
        """喂入一个字节，返回解析出的 (cmd, data) 列表。"""
        out = []                                 # 本次解析结果
        if self.state == "sof1":                 # 等待帧头1
            if byte == 0xAA:                     # 匹配0xAA
                self.state = "sof2"              # 进入等待帧头2
        elif self.state == "sof2":               # 等待帧头2
            if byte == 0x55:                     # 匹配0x55
                self.state = "len"               # 进入读长度
            elif byte != 0xAA:                   # 不是帧头且不是0xAA
                self.state = "sof1"              # 回到初始
        elif self.state == "len":                # 读长度
            if 1 <= byte <= 80:                  # 长度合法
                self.need = byte                 # 还需要读CMD+DATA
                self.length = byte               # 保存LEN，校验时要用
                self.buf.clear()                 # 清空缓存
                self.state = "body"              # 进入读正文
            else:
                self.state = "sof1"              # 非法长度
        elif self.state == "body":               # 读CMD+DATA
            self.buf.append(byte)                # 存入
            self.need -= 1                       # 剩余减1
            if self.need == 0:                   # 读完了
                self.state = "check"             # 进入读校验
        elif self.state == "check":              # 读校验
            body = bytes(self.buf)               # 取出正文
            if body and checksum(bytes([self.length]) + body) == byte:  # 校验通过（LEN也要参与）
                out.append((body[0], body[1:]))  # 返回 cmd 和 data
            self.state = "sof1"                  # 回到初始
        return out                               # 返回结果


# ===== 指令构造 =====

def cmd_manual(vx: float, vy: float, wz: float) -> bytes:
    """手动全向速度：vx/vy 单位 m/s，wz 单位 rad/s，按0.001缩放。"""
    data = struct.pack("<hhh",                    # 三个有符号16位
                       int(vx * 1000),            # 前后速度
                       int(vy * 1000),            # 左右速度
                       int(wz * 1000))            # 旋转速度
    return build_frame(config.CMD_MANUAL, data)   # 组帧


def cmd_brake_fast() -> bytes:
    """急刹停。"""
    return build_frame(config.CMD_BRAKE_FAST)     # 无数据


def cmd_brake_soft(decel: int = 0) -> bytes:
    """缓停：decel 为减速档位（0=默认）。"""
    return build_frame(config.CMD_BRAKE_SOFT, bytes([decel & 0xFF]))   # 1字节


def cmd_pid_stop(target_mm: int) -> bytes:
    """PID精准停：目标相对距离，单位mm。"""
    data = struct.pack("<h", int(target_mm))      # 有符号16位
    return build_frame(config.CMD_PID_STOP, data) # 组帧


def cmd_route(side_mm: int) -> bytes:
    """启动正方形路线：side_mm 为边长，按100mm为单位下发。"""
    side_unit = max(1, min(255, int(round(side_mm / 100.0))))   # 换算成0.1m单位
    return build_frame(config.CMD_ROUTE, bytes([0, side_unit])) # route_id=0


def cmd_stop_all() -> bytes:
    """急停（全停）。"""
    return build_frame(config.CMD_STOP_ALL)       # 无数据


def cmd_set_pos_pid(kp: float, ki: float, kd: float) -> bytes:
    """设置位置环PID，参数×1000后下发。"""
    data = struct.pack("<HHH",                    # 三个无符号16位
                       int(kp * 1000),            # Kp
                       int(ki * 1000),            # Ki
                       int(kd * 1000))            # Kd
    return build_frame(config.CMD_SET_POS_PID, data)   # 组帧


def cmd_rotate(angle_deg: float) -> bytes:
    """原地旋转指定角度：正=左转/逆时针，负=右转/顺时针，单位0.1度。"""
    data = struct.pack("<h", int(round(angle_deg * 10.0)))   # 度 -> 0.1度
    return build_frame(config.CMD_ROTATE_ANGLE, data)        # 组帧

def cmd_set_accel(v_accel: float, w_accel: float) -> bytes:
    """设置线/角加速度限制：值越大越接近急停急行。"""
    data = struct.pack("<HH", int(v_accel * 1000), int(w_accel * 1000))   # 两个u16
    return build_frame(config.CMD_SET_ACCEL, data)                        # 组帧

def cmd_enc_zero() -> bytes:
    """编码器清零。"""
    return build_frame(config.CMD_ENC_ZERO)       # 无数据


def cmd_heartbeat() -> bytes:
    """心跳。"""
    return build_frame(config.CMD_HEARTBEAT)      # 无数据


def cmd_read_params() -> bytes:
    """读取参数。"""
    return build_frame(config.CMD_READ_PARAMS)    # 无数据


def cmd_set_limits(vmax: float, wmax: float) -> bytes:
    """设置最大线速度/角速度。"""
    data = struct.pack("<HH", int(vmax * 1000), int(wmax * 1000))   # 两个u16
    return build_frame(config.CMD_SET_LIMITS, data)                 # 组帧


# ===== 回报解析 =====

def parse_status(data: bytes):
    """解析0x81状态帧：mode, battery, enc[4], speed[4]。"""
    if len(data) < 27:                            # 长度不够
        return None
    mode = data[0]                                # 模式
    battery = struct.unpack_from("<H", data, 1)[0]  # 电压
    enc = list(struct.unpack_from("<iiii", data, 3))  # 四轮累计计数
    spd = list(struct.unpack_from("<hhhh", data, 19)) # 四轮速度（0.001m/s）
    return {"mode": mode, "battery": battery, "enc": enc,
            "speed": [s / 1000.0 for s in spd]}   # 速度换算成m/s


def parse_curve(data: bytes):
    """解析0x82曲线帧：目标[4] + 实际[4]。"""
    if len(data) < 16:                            # 长度不够
        return None
    tgt = struct.unpack_from("<hhhh", data, 0)    # 目标速度
    act = struct.unpack_from("<hhhh", data, 8)    # 实际速度
    return {"target": [v / 1000.0 for v in tgt],
            "actual": [v / 1000.0 for v in act]}


def parse_ack(data: bytes):
    """解析0x83 ACK：ack_cmd, err。"""
    if len(data) < 2:                             # 长度不够
        return None
    return {"cmd": data[0], "err": data[1]}       # 返回指令和错误码


def parse_params(data: bytes):
    """解析0x85参数帧：位置PID + 限幅。"""
    if len(data) < 16:                            # 长度不够
        return None
    vals = struct.unpack_from("<HHHHHHHH", data, 0)   # 8个u16
    return {"kp": vals[0] / 1000.0, "ki": vals[1] / 1000.0, "kd": vals[2] / 1000.0,
            "vmax": vals[6] / 1000.0, "wmax": vals[7] / 1000.0}



