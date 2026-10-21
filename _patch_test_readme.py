from pathlib import Path
p=Path('Test_Project/README.md')
t=p.read_text(encoding='utf-8-sig')
t=t.replace('| `ramp <v0> <v1> <accel>` | 打印加速度平滑时间线 |\r\n','').replace('| `ramp <v0> <v1> <accel>` | 打印加速度平滑时间线 |\n','')
t=t.replace('debug_algo.c/h   纯算法：麦轮/CPR/旋转/平滑','debug_algo.c/h   纯算法：麦轮/CPR/旋转')
p.write_text(t,encoding='utf-8')
print('test readme updated')
