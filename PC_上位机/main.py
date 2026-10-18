# -*- coding: utf-8 -*-
"""上位机程序入口。"""

import sys                                     # 系统参数
from PySide6.QtWidgets import QApplication     # Qt应用
from ui.main_window import MainWindow          # 主窗口


def main():
    """启动应用。"""
    app = QApplication(sys.argv)               # 创建应用
    app.setApplicationName("MecanumCarConsole")# 应用名
    window = MainWindow()                      # 主窗口
    window.show()                              # 显示
    sys.exit(app.exec())                       # 进入事件循环


if __name__ == "__main__":                     # 直接运行
    main()                                     # 启动
