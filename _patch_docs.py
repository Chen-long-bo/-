from pathlib import Path

# 教学手册：加入变更说明并同步实车辊轮方向
p=Path('教学手册.md')
t=p.read_text(encoding='utf-8-sig')
note='> 2026-10-21 变更：普通手动、固定路线和旋转已取消缓起/缓停；PID 只在“控制与测试”页使用。车轮辊轮方向按 `车轮布局.jpg`：A `/`，B `\\`，C `\\`，D `/`（俯视图）。'
if '2026-10-21 变更' not in t:
    lines=t.splitlines()
    lines.insert(1, note)
    t='\n'.join(lines)+'\n'
t=t.replace('左、右两侧辊轮互为镜像','按实车图：A /，B \\，C \\，D /（俯视图）')
t=t.replace('你的实车已经确认：左侧前后轮辊轮方向一致，右侧前后轮方向一致，并且左右互为镜像（X 型布局）。','按 `车轮布局.jpg` 的俯视图：A 轮辊轮向右上（/），B 轮向右下（\\），C 轮向右下（\\），D 轮向右上（/）。电机方向、编码器方向和代码符号仍要分别验证。')
t=t.replace('| U2 | 辊轮方向 | 左右镜像的 X 型布局 | 看四个轮子辊轮排列，单轮测试 |','| U2 | 辊轮方向 | A `/`，B `\\`，C `\\`，D `/`（按车轮布局.jpg） | 对照图片、单轮测试和整车横移/旋转测试 |')
p.write_text(t,encoding='utf-8')

# 参数手册：历史内容提示
p=Path('参数手册.md')
t=p.read_text(encoding='utf-8-sig')
note='> **2026-10-21 变更提示**：普通手动、固定路线、旋转已删除缓起/缓停和加速度平滑；`0x03`、`0x0E`、`CFG_ACCEL_*`、`CFG_SOFT_BRAKE_DECEL` 已从当前固件删除。本文中如仍有这些历史条目，仅作为旧版本记录；当前参数以 `上位机参数调节页` 和 `本次修改说明_2026-10-21.md` 为准。\n\n'
if '2026-10-21 变更提示' not in t:
    t=note+t
p.write_text(t,encoding='utf-8')

# 代码地图：提示当前版本变化
p=Path('代码地图.md')
t=p.read_text(encoding='utf-8-sig')
note='> **2026-10-21 变更提示**：当前版本已删除普通控制中的缓起/缓停和加速度平滑；PID 仅保留在控制与测试页。本文部分“平滑/ramp”描述属于历史版本，以实际源码和 `本次修改说明_2026-10-21.md` 为准。\n\n'
if '2026-10-21 变更提示' not in t:
    t=note+t
p.write_text(t,encoding='utf-8')
print('docs notes updated')
