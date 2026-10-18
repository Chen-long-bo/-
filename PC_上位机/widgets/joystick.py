# -*- coding: utf-8 -*-
"""虚拟摇杆控件：鼠标拖动输出 -1~1 的 x/y。"""

from PySide6.QtCore import Qt, Signal, QPointF   # Qt核心
from PySide6.QtGui import QPainter, QColor, QPen, QBrush   # 绘图
from PySide6.QtWidgets import QWidget            # 控件基类
import config                                    # 配置


class Joystick(QWidget):
    """圆形虚拟摇杆。"""

    changed = Signal(float, float)               # 摇杆变化信号（x, y）

    def __init__(self, parent=None):
        super().__init__(parent)                 # 父类初始化
        self.setMinimumSize(240, 240)            # 最小尺寸
        self.x = 0.0                             # 归一化x
        self.y = 0.0                             # 归一化y
        self._dragging = False                   # 是否正在拖动
        self.setMouseTracking(True)              # 开启鼠标跟踪

    def reset(self):
        """回中。"""
        self.x = 0.0                             # x归零
        self.y = 0.0                             # y归零
        self.update()                            # 重绘
        self.changed.emit(0.0, 0.0)              # 发出信号

    def _set_from_pos(self, pos: QPointF):
        """根据鼠标位置更新摇杆。"""
        cx = self.width() / 2.0                  # 圆心x
        cy = self.height() / 2.0                 # 圆心y
        radius = min(self.width(), self.height()) / 2.0 - 18.0   # 可用半径
        dx = (pos.x() - cx) / radius             # 归一化dx
        dy = (pos.y() - cy) / radius             # 归一化dy
        dist = (dx * dx + dy * dy) ** 0.5        # 距离
        if dist > 1.0:                           # 超出范围
            dx /= dist                           # 拉回圆内
            dy /= dist                           # 拉回圆内
        self.x = max(-1.0, min(1.0, dx))         # 限幅
        self.y = max(-1.0, min(1.0, -dy))        # y向上为正
        self.update()                            # 重绘
        self.changed.emit(self.x, self.y)        # 发出信号

    def mousePressEvent(self, event):
        """按下鼠标开始拖动。"""
        if event.button() == Qt.LeftButton:      # 左键
            self._dragging = True                # 标记拖动
            self._set_from_pos(event.position()) # 更新

    def mouseMoveEvent(self, event):
        """拖动鼠标。"""
        if self._dragging:                       # 正在拖动
            self._set_from_pos(event.position()) # 更新

    def mouseReleaseEvent(self, event):
        """松开鼠标回中。"""
        if event.button() == Qt.LeftButton:      # 左键
            self._dragging = False               # 取消拖动
            self.reset()                         # 回中

    def mouseDoubleClickEvent(self, event):
        """双击回中。"""
        self.reset()                             # 回中

    def paintEvent(self, event):
        """绘制摇杆。"""
        p = QPainter(self)                       # 画笔
        p.setRenderHint(QPainter.Antialiasing)   # 抗锯齿
        cx = self.width() / 2.0                  # 圆心x
        cy = self.height() / 2.0                 # 圆心y
        radius = min(self.width(), self.height()) / 2.0 - 18.0   # 半径
        p.setBrush(QBrush(QColor(config.COLOR_PANEL_2)))         # 底色
        p.setPen(QPen(QColor(config.COLOR_BORDER), 2))           # 边框
        p.drawEllipse(QPointF(cx, cy), radius, radius)           # 外圆
        p.setPen(QPen(QColor(config.COLOR_BORDER), 1, Qt.DashLine))   # 虚线
        p.drawLine(QPointF(cx - radius, cy), QPointF(cx + radius, cy)) # 横线
        p.drawLine(QPointF(cx, cy - radius), QPointF(cx, cy + radius)) # 竖线
        kx = cx + self.x * radius                # 摇杆头x
        ky = cy - self.y * radius                # 摇杆头y
        p.setBrush(QBrush(QColor(config.COLOR_ACCENT)))          # 摇杆头颜色
        p.setPen(QPen(QColor(config.COLOR_ACCENT).lighter(130), 2))   # 摇杆头边框
        p.drawEllipse(QPointF(kx, ky), 26, 26)   # 摇杆头
        p.setPen(QPen(QColor(config.COLOR_SUBTEXT), 1))           # 文字颜色
        p.drawText(10, self.height() - 10, "拖动 / 双击回中")      # 提示文字
