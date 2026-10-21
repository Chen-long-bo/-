from pathlib import Path
p=Path('README.md')
t=p.read_text(encoding='utf-8-sig')
line='- [本次修改说明（2026-10-21）](本次修改说明_2026-10-21.md) —— 按键遥控、PID 分离、参数页、缓起缓停删除和烧录结果'
if '本次修改说明' not in t:
    t=t.replace('- [改造方案与阶段进度](改造方案大纲_v1.md)', line+'\n- [改造方案与阶段进度](改造方案大纲_v1.md)')
p.write_text(t,encoding='utf-8')
print('README linked')
