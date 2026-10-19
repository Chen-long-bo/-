# 硬件测试 / 算法标定工程（MecanumTest）

> 独立于主工程的调试工程：通过 COM5（USB转串口，115200）发送 ASCII 命令，
> 直接测试驱动模块、编码器、运动学、旋转标定、最小驱动、PID 仿真等。
> 不需要 Keil 在线调试，也不依赖上位机。

## 一、烧录

1. 用 Keil 打开 `Test_Project\MecanumTest\MDK-ARM\MecanumTest.uvprojx`；
2. 点 `Flash → Download` 烧录；
3. 已编译好的固件：`MDK-ARM\MecanumTest\MecanumTest.hex`。

## 二、连接

- USB转串口接 COM5；
- 串口助手：**115200, 8N1**；
- 复位开发板，应看到：
  `=== Mecanum Test / Debug ready ===`

## 三、命令表

### 基础测试

| 命令 | 说明 |
|---|---|
| `help` | 帮助 |
| `stop` | 停车 |
| `bat` | 读电池电压 |
| `enc` | 读编码器（20ms + 累计） |
| `enczero` | 编码器清零 |
| `car <vx> <vy> <wz>` | 整车速度（m/s, m/s, rad/s） |
| `wheel <0-3> <speed>` | 单轮速度（0=A 1=B 2=C 3=D，-1~1） |
| `raw <text>` | 直接把文本发给驱动模块（自动补 `!`） |
| `link` | 链路自检 + 读电压 |

### 算法/标定

| 命令 | 说明 |
|---|---|
| `mecanum <vx> <vy> <wz>` | 只做麦轮逆解算，不驱动；打印四轮 m/s |
| `geo <vx> <vy> <wz> <wb_mm> <track_mm>` | 用自定义轴距/轮距预览四轮速度 |
| `cpcal <mm>` | 由当前相对计数和实际距离反算建议 CPR |
| `rot90 [speed] [ms]` | 左转 90° 脉冲（默认 0.6, 900ms；负速度=右转） |
| `rotcal <measured_deg>` | 由实测角度反算建议 90° 时间 |
| `min <speed>` | 低速脉冲 1.5s，用于找最小平稳驱动 |
| `sign [0-3] [1/-1]` | 显示/设置单轮方向符号 |
| `ramp <v0> <v1> <accel>` | 打印加速度平滑时间线 |
| `pidstep <kp> <ki> <kd> <target>` | PID 阶跃仿真（位置/输出） |

## 四、当前硬件结论（2026-10-19）

- 四个电机可转；
- 四个编码器均可读数；
- 速度低于约 0.3（归一化）时容易震动，主固件已加入最小驱动 0.3；
- 具体 CPR、旋转时间、PID 仍需按 `参数手册.md` 标定。

## 五、工程结构

```text
MecanumTest/
├─ Core/       CubeMX 生成（串口初始化等）
├─ Drivers/    HAL 库
├─ MDK-ARM/    Keil 工程
└─ Test/       测试/调试代码
   ├─ config.h         参数
   ├─ driver_comm.c/h  驱动模块串口通信
   ├─ chassis_control.c/h 麦轮运动学
   ├─ bsp_encoder.c/h  编码器读取
   ├─ debug_algo.c/h   纯算法：麦轮/CPR/旋转/平滑
   ├─ pid.c/h          PID（用于 pidstep 仿真）
   └─ test_app.c/h     ASCII 命令接口
```
