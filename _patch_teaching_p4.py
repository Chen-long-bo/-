from pathlib import Path
p=Path('教学手册.md')
t=p.read_text(encoding='utf-8-sig')
old='''### P4：平滑和低速

- 调 `CFG_MIN_DRIVE`；
- 调 `CFG_ACCEL_V/CFG_ACCEL_W`；
- 观察起步、停车、震动。'''
new='''### P4：低速与安全

- 调 `CFG_MIN_DRIVE`；
- 观察低速是否震动、起步是否过猛；
- 确认松开按键立即停止；
- 确认急停/通信超时后能够安全停车。'''
t=t.replace(old,new)
p.write_text(t,encoding='utf-8')
print('P4 updated')
