# 硬件测试工程（Test_Project）

> 独立于主工程的硬件测试程序，通过 COM5（USB转串口，115200）发送文本命令即可测试，
> 不用 Keil、不用调试器。

## 一、怎么用

1. 用 Keil 打开 `Test_Project\MecanumTest\MDK-ARM\MecanumTest.uvprojx`，点 `Flash → Download` 烧录。
   （已编译好的固件在 `...\MDK-ARM\MecanumTest\MecanumTest.hex`）
2. 打开任意串口助手，选 **COM5，115200**，复位开发板，会看到：
   `=== Mecanum Test ready ===`
3. 在串口助手发送下面的命令（每条命令后面回车）。

## 二、命令列表

| 命令 | 说明 |
|---|---|
| `help` | 帮助 |
| `stop` | 停车 |
| `bat` | 读电池电压 |
| `enc` | 读编码器（20ms 和累计） |
| `enczero` | 编码器累计清零 |
| `car <vx> <vy> <wz>` | 整车速度：前后 m/s、左右 m/s、旋转 rad/s |
| `wheel <0-3> <speed>` | 单轮速度：0=A 1=B 2=C 3=D，speed 范围 -1~1 |
| `raw <文本>` | 把文本原样发给驱动模块（调试用） |

示例：
- `car 0.2 0 0` → 以 0.2 m/s 前进
- `car 0 0 0.5` → 原地旋转
- `wheel 0 0.3` → 只让 A 轮转

## 三、当前测试结论（2026-10-16）

- 电机：4 个都能转。
- 编码器：B、C、D 正常计数；**A 轮编码器没数据**（累计一直不变，20ms 为0）→ 待查 A 电机 6P 插头的编码器线（蓝Vcc/黑GND/绿A/黄B）。
- 电池电压：约 12.3V 正常。

## 四、工程结构

```text
MecanumTest/
├─ Core/       CubeMX 生成（串口初始化等）
├─ Drivers/    HAL 库
├─ MDK-ARM/    Keil 工程
└─ Test/       测试代码
   ├─ config.h         参数
   ├─ driver_comm.c/h  驱动模块串口通信
   ├─ chassis_control.c/h 麦轮运动学
   ├─ bsp_encoder.c/h  编码器读取
   └─ test_app.c/h     ASCII 命令接口
```
