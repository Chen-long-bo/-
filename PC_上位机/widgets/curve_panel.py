# -*- coding: utf-8 -*-
"""实时曲线面板：显示四轮目标/实际速度。"""

import collections                              # 双端队列
import pyqtgraph as pg                          # 高性能绘图
from PySide6.QtWidgets import QVBoxLayout, QWidget   # 布局
import config                                   # 配置


class CurvePanel(QWidget):
    """四轮速度曲线。"""

    def __init__(self, parent=None):
        super().__init__(parent)                # 父类初始化
        layout = QVBoxLayout(self)              # 垂直布局
        layout.setContentsMargins(0, 0, 0, 0)   # 无边距
        pg.setConfigOptions(antialias=True)     # 开启抗锯齿
        self.plot = pg.PlotWidget()             # 绘图控件
        self.plot.setBackground(config.COLOR_PANEL)      # 背景色
        self.plot.showGrid(x=True, y=True, alpha=0.18)   # 网格
        self.plot.setLabel("left", "速度 (m/s)")         # Y轴
        self.plot.setLabel("bottom", "采样点")           # X轴
        self.plot.addLegend(offset=(10, 10))             # 图例
        layout.addWidget(self.plot)             # 加入布局
        self.data_actual = [collections.deque(maxlen=config.CURVE_MAX_POINTS) for _ in range(4)]   # 实际速度缓存
        self.data_target = [collections.deque(maxlen=config.CURVE_MAX_POINTS) for _ in range(4)]   # 目标速度缓存
        self.curves_actual = []                 # 实际曲线
        self.curves_target = []                 # 目标曲线
        names = ["A", "B", "C", "D"]            # 轮子名称
        for i in range(4):                      # 创建四条实际曲线
            color = config.WHEEL_COLORS[i]      # 颜色
            c = self.plot.plot(pen=pg.mkPen(color, width=2), name=f"{names[i]} 实际")   # 实际
            self.curves_actual.append(c)        # 保存
            t = self.plot.plot(pen=pg.mkPen(color, width=1, style=pg.QtCore.Qt.DashLine), name=f"{names[i]} 目标")   # 目标虚线
            self.curves_target.append(t)        # 保存
        self.index = 0                          # 采样序号

    def update_data(self, target, actual):
        """追加一组数据并重绘。"""
        self.index += 1                         # 序号加1
        for i in range(4):                      # 四轮
            self.data_actual[i].append(actual[i])   # 存实际
            self.data_target[i].append(target[i])   # 存目标
            self.curves_actual[i].setData(list(self.data_actual[i]))   # 更新实际曲线
            self.curves_target[i].setData(list(self.data_target[i]))   # 更新目标曲线

    def clear(self):
        """清空曲线。"""
        for i in range(4):                      # 四轮
            self.data_actual[i].clear()         # 清实际
            self.data_target[i].clear()         # 清目标
            self.curves_actual[i].setData([])   # 清图
            self.curves_target[i].setData([])   # 清图
        self.index = 0                          # 序号归零
