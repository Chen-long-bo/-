# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\改造方案大纲_v1.md"
c = open(p, encoding="utf-8").read()
c = c.replace("- 适配桌面浏览器，可选手机适配。", "- 适配桌面浏览器 + **手机适配（已确认必须做）**。")
c = c.replace("> 请确认是否需要手机适配、是否需要深色/浅色切换。", "> 手机适配已确认必须做；深色/浅色切换待定。")
c = c.replace("- 图表用 Canvas/SVG；\\n- **算法内容特别标注**：所有算法模块/参数/公式用 `【算法】` 标签和独立页面重点展示；",
              "- 图表用 Canvas/SVG；\n- **算法内容特别标注**：所有算法模块/参数/公式用 `【算法】` 标签和独立页面重点展示；")
open(p, "w", encoding="utf-8").write(c)
print("fixed")
