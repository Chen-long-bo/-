from pathlib import Path
p=Path('visualization/README.md')
t=p.read_text(encoding='utf-8-sig')
note='> 2026-10-21：普通手动、固定路线、旋转不使用 PID，也不使用缓起/缓停；PID 仅在控制与测试页使用。网站中的历史手册段落已标记为旧版本。\n\n'
if '2026-10-21' not in t:
    t=note+t
p.write_text(t,encoding='utf-8')
print('visualization readme updated')
