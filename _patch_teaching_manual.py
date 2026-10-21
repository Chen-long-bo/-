from pathlib import Path
import re
p=Path('教学手册.md')
t=p.read_text(encoding='utf-8-sig')
t=re.sub(r'^\| `0x03`.*\n', '', t, flags=re.M)
t=re.sub(r'^\| `0x0E`.*\n', '', t, flags=re.M)
t=re.sub(r'^\| `CFG_ACCEL_V`.*\n', '', t, flags=re.M)
t=re.sub(r'^\| `CFG_ACCEL_W`.*\n', '', t, flags=re.M)
t=re.sub(r'^\| `CFG_SOFT_BRAKE_DECEL`.*\n', '', t, flags=re.M)
t=re.sub(r'^\| `g_ramp_vx/vy/wz`.*\n', '', t, flags=re.M)
t=re.sub(r'^\| `g_accel_v/w`.*\n', '', t, flags=re.M)
t=t.replace('→ RampToward() 做加速度平滑','→ 直接发送目标速度（普通控制不使用平滑）')
t=t.replace('MANUAL：平滑 + 逆运动学 + $Car','MANUAL：直接速度 + 逆运动学 + $Car')
t=t.replace('| `g_mode` | 当前模式 | IDLE/MANUAL/BRAKE_SOFT/POS_STOP/ROUTE/ROTATE_ANGLE |','| `g_mode` | 当前模式 | IDLE/MANUAL/POS_STOP/ROUTE/ROTATE_ANGLE |')
t=t.replace('| `CFG_DRIVER_BAUD` | 115200 | bps | 注释上的驱动模块波特率 | 当前 `usart.c` 仍硬编码，改宏不一定生效 |','| `CFG_DRIVER_BAUD` | 115200 | bps | USART2 与驱动模块的波特率 | 必须与驱动模块实际波特率一致 |')
t=t.replace('| `CFG_DEBUG_BAUD` | 115200 | bps | 注释上的调试波特率 | 当前 `usart.c` 仍硬编码 |','| `CFG_DEBUG_BAUD` | 115200 | bps | USART3 有线调试波特率 | 必须与 USB 转串口一致 |')
t=t.replace('| 运行期参数 | 上位机 PID/调试中心 | 点下发，掉电可能丢失 | 位置 PID、限幅、加速度 |','| 运行期参数 | 上位机 PID/调试中心 | 点下发，掉电可能丢失 | 位置 PID、限幅 |')
t=t.replace('5. 再改控制参数（最小驱动、加速度、PID）；','5. 再改控制参数（最小驱动、PID）；')
t=t.replace('`RampToward` 和 PID 的区别是什么？','普通直接速度控制和 PID 的区别是什么？')
start=t.find('### 5.5 【算法】加速度平滑')
end=t.find('### 5.6 三种停止方式')
if start!=-1 and end!=-1:
    new='''### 5.5 缓起缓停已删除

2026-10-21 版本已删除普通手动、固定路线和旋转中的缓起/缓停及速度斜坡。

当前普通控制直接执行目标速度；需要平滑效果时，应在控制与测试页通过 PID 参数和机械标定获得稳定响应。
'''
    t=t[:start]+new+'\n'+t[end:]
start=t.find('### 5.6 三种停止方式')
end=t.find('### 5.7 【算法】原地旋转与时间标定')
if start!=-1 and end!=-1:
    new='''### 5.6 停止方式

| 方式 | 代码行为 | 现象 | 适用场景 |
|---|---|---|---|
| 急刹停 | `Motor_Stop()` 发零速度，模式回 IDLE | 立即停，可能有惯性冲击 | 紧急情况、测试 |
| PID 位置停 | 位置环 + 编码器距离反馈 | 走到指定距离后停 | 控制与测试页 |

注意：本工程所说的“急刹”是让驱动模块目标速度归零，不是机械抱闸；轮子仍会因惯性滑行一小段。
'''
    t=t[:start]+new+'\n'+t[end:]
p.write_text(t,encoding='utf-8')
print('teaching manual control sections updated')
