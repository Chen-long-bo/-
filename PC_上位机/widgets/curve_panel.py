# -*- coding: utf-8 -*-
"""实时曲线面板：四轮速度 + PID 位置/误差。"""

import collections                              # 双端队列
import pyqtgraph as pg                          # 高性能绘图
from PySide6.QtWidgets import QVBoxLayout, QWidget   # 布局
import config                                   # 配置


class CurvePanel(QWidget):
    """上方显示四轮速度，下方显示 PID 目标位置、实际位置和误差。"""

    def __init__(self, parent=None):
        super().__init__(parent)                # 父类初始化
        layout = QVBoxLayout(self)              # 垂直布局
        layout.setContentsMargins(0, 0, 0, 0)   # 无边距
        layout.setSpacing(8)                    # 两块图的间距
        pg.setConfigOptions(antialias=True)     # 开启抗锯齿

        self.speed_plot = pg.PlotWidget()       # 速度曲线图
        self.speed_plot.setBackground(config.COLOR_PANEL)      # 背景色
        self.speed_plot.showGrid(x=True, y=True, alpha=0.18)   # 网格
        self.speed_plot.setLabel("left", "速度 (m/s)")          # Y轴
        self.speed_plot.setLabel("bottom", "采样点")            # X轴
        self.speed_plot.addLegend(offset=(10, 10))              # 图例
        layout.addWidget(self.speed_plot, 1)    # 加入速度图

        self.position_plot = pg.PlotWidget()    # 位置曲线图
        self.position_plot.setBackground(config.COLOR_PANEL)   # 背景色
        self.position_plot.showGrid(x=True, y=True, alpha=0.18) # 网格
        self.position_plot.setLabel("left", "位置 / 误差 (mm)") # Y轴
        self.position_plot.setLabel("bottom", "采样点")          # X轴
        self.position_plot.addLegend(offset=(10, 10))            # 图例
        layout.addWidget(self.position_plot, 1)  # 加入位置图

        self.data_actual = [collections.deque(maxlen=config.CURVE_MAX_POINTS) for _ in range(4)]   # 实际速度缓存
        self.data_target = [collections.deque(maxlen=config.CURVE_MAX_POINTS) for _ in range(4)]   # 目标速度缓存
        self.data_position_target = collections.deque(maxlen=config.CURVE_MAX_POINTS)   # 目标位置缓存
        self.data_position_actual = collections.deque(maxlen=config.CURVE_MAX_POINTS)   # 实际位置缓存
        self.data_position_error = collections.deque(maxlen=config.CURVE_MAX_POINTS)    # 位置误差缓存
        self.curves_actual = []                 # 实际速度曲线
        self.curves_target = []                 # 目标速度曲线

        names = ["A", "B", "C", "D"]            # 轮子名称
        for i in range(4):                      # 创建四轮速度曲线
            color = config.WHEEL_COLORS[i]      # 颜色
            actual_curve = self.speed_plot.plot(pen=pg.mkPen(color, width=2), name=f"{names[i]} 实际")       # 实际速度
            target_curve = self.speed_plot.plot(pen=pg.mkPen(color, width=1, style=pg.QtCore.Qt.DashLine), name=f"{names[i]} 目标")   # 目标速度
            self.curves_actual.append(actual_curve)   # 保存实际曲线
            self.curves_target.append(target_curve)   # 保存目标曲线

        self.curve_pos_target = self.position_plot.plot(pen=pg.mkPen(config.COLOR_ACCENT, width=2, style=pg.QtCore.Qt.DashLine), name="目标位置")   # 目标位置
        self.curve_pos_actual = self.position_plot.plot(pen=pg.mkPen(config.COLOR_YELLOW, width=2), name="实际位置")   # 实际位置
        self.curve_pos_error = self.position_plot.plot(pen=pg.mkPen(config.COLOR_BLUE, width=1.5), name="位置误差")   # 位置误差
        self.index = 0                          # 采样序号

    def update_data(self, target, actual):
        """追加一组四轮速度数据。"""
        self.index += 1                         # 序号加1
        for i in range(4):                      # 四轮
            self.data_actual[i].append(actual[i])   # 存实际速度
            self.data_target[i].append(target[i])   # 存目标速度
            self.curves_actual[i].setData(list(self.data_actual[i]))   # 更新实际曲线
            self.curves_target[i].setData(list(self.data_target[i]))   # 更新目标曲线

    def update_position(self, target_mm, actual_mm, error_mm):
        """追加一组 PID 位置数据，单位均为 mm。"""
        self.data_position_target.append(target_mm)       # 存目标位置
        self.data_position_actual.append(actual_mm)       # 存实际位置
        self.data_position_error.append(error_mm)         # 存位置误差
        self.curve_pos_target.setData(list(self.data_position_target))   # 更新目标位置
        self.curve_pos_actual.setData(list(self.data_position_actual))   # 更新实际位置
        self.curve_pos_error.setData(list(self.data_position_error))     # 更新位置误差

    def clear(self):
        """清空全部曲线。"""
        for i in range(4):                      # 四轮
            self.data_actual[i].clear()         # 清实际速度
            self.data_target[i].clear()         # 清目标速度
            self.curves_actual[i].setData([])   # 清实际速度图
            self.curves_target[i].setData([])   # 清目标速度图
        self.data_position_target.clear()       # 清目标位置
        self.data_position_actual.clear()       # 清实际位置
        self.data_position_error.clear()        # 清位置误差
        self.curve_pos_target.setData([])       # 清目标位置图
        self.curve_pos_actual.setData([])       # 清实际位置图
        self.curve_pos_error.setData([])        # 清位置误差图
        self.index = 0                          # 序号归零
