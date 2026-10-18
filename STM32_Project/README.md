# STM32 工程骨架说明（第2步）

本目录是 STM32 下位机工程骨架。你还需要用 STM32CubeMX 生成 HAL 库工程，再把 `User` 文件夹里的文件加进去编译。

## 文件结构

```text
STM32_Project/
├─ CubeMX配置说明.md    ← 一步一步照着做
├─ README.md            ← 本文件
└─ User/                ← 我们写的全部用户代码
   ├─ config.h          所有可调参数（调这里）
   ├─ bsp_bluetooth.c/h 蓝牙协议收发
   ├─ driver_comm.c/h   与驱动模块的串口通信层（内部支撑模块）
   ├─ bsp_motor.c/h     电机PWM输出
   ├─ bsp_encoder.c/h   编码器读取/换算
   ├─ chassis_control.c/h 麦克纳姆轮运动学
   ├─ pid.c/h           PID控制器
   ├─ control_mode.c/h  运行模式与串级PID主循环
   ├─ route.c/h         固定路线（正方形，占位）
   └─ user_app.c/h      总入口：User_Init / User_Loop
```

## 模块关系（数据流向）

```text
上位机(PC)
   │ 蓝牙SPP 9600（USART1）
   v
bsp_bluetooth（解析协议）
   │ cmd
   v
control_mode（运行模式 + 速度/位置串级PID）
   ├── chassis_control（麦轮逆运动学）
   ├── pid（PID计算）
   ├── bsp_encoder（读编码器速度/位置）
   └── bsp_motor（输出PWM）
         │
         v
driver_comm（USART2 115200，发命令/收编码器）
         │
         v
四路编码器电机驱动模块
```

## 可调参数在哪里

- 全部集中在 `User/config.h`，改完重新编译烧录即可。
- 详细步骤见同目录 `CubeMX配置说明.md`。
