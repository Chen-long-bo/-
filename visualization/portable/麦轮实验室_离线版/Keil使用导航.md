# Keil uVision5 使用导航（零基础版）

> 目标：让你知道 **Keil 界面每个区域是什么、怎么打开工程、怎么编译、怎么烧录、怎么调试、怎么用测试工程**。
> 配套示意图：`diagrams/keil_ui.svg`（建议先打开看图）。

---

## 1. 先分清两个 Keil 工程

工程目录里有两个 `.uvprojx`：

| 工程 | 路径 | 用途 |
|---|---|---|
| 主工程 | `STM32_Project\CubeMX\MecanumCar\MDK-ARM\MecanumCar.uvprojx` | 真正跑小车的固件：蓝牙控制、麦轮、PID、路线 |
| 测试工程 | `Test_Project\MecanumTest\MDK-ARM\MecanumTest.uvprojx` | 调试/标定用：单轮、编码器、CPR、旋转、最小驱动、PID 仿真 |

> 同一时间，板子里只能有其中一套固件。  
> 烧了测试工程，主工程就不在板子里；要跑小车，需要重新烧主工程。

---

## 2. Keil 界面导航

打开 Keil 后，主要看 5 个区域（见 `diagrams/keil_ui.svg`）：

1. **菜单栏**：File / Edit / View / Project / Flash / Debug / Peripherals / Tools / Window / Help；
2. **工具栏**：Build（编译）、Rebuild（全编译）、Download（烧录）、Debug（调试）、Options（魔术棒）；
3. **Project 工程树（左侧）**：显示 Target、Groups、源文件；
4. **Editor 代码区（中间）**：双击左侧文件后在这里显示代码；
5. **Build Output 编译输出（底部）**：显示编译错误/警告/成功信息。

### 最常用的 5 个操作

| 操作 | 怎么做 | 成功标志 |
|---|---|---|
| 编译 | 点工具栏 **Build** 或按 **F7** | 底部出现 `0 Error(s), 0 Warning(s)` |
| 全编译 | 点 **Rebuild** | 同上 |
| 烧录 | 点 **Download** 或按 **F8** | `Erase Done / Programming Done / Verify OK` |
| 调试 | 点 **Debug** 或按 **Ctrl+F5** | 进入调试界面，出现黄色箭头/断点 |
| 退出调试 | 再按 **Ctrl+F5** | 回到普通编辑界面 |

---

## 3. 打开工程

### 3.1 打开主工程

1. 打开文件资源管理器；
2. 进入：
   `D:\CODEX-WORK\蓝牙遥控麦轮小车\STM32_Project\CubeMX\MecanumCar\MDK-ARM\`
3. 双击 `MecanumCar.uvprojx`；
4. Keil 打开后，左侧 Project 树应出现 `Target 1: MecanumCar`。

### 3.2 打开测试工程

1. 进入：
   `D:\CODEX-WORK\蓝牙遥控麦轮小车\Test_Project\MecanumTest\MDK-ARM\`
2. 双击 `MecanumTest.uvprojx`；
3. 左侧 Project 树应出现 `Target 1: MecanumTest`。

> 如果双击没反应，打开 Keil → `Project → Open Project...` → 选择 `.uvprojx`。

---

## 4. 看懂左侧文件树

主工程大致长这样：

```text
Target 1: MecanumCar
├─ Application/MDK-ARM
├─ Application/User/Core
│  ├─ main.c              ← 程序入口
│  ├─ usart.c             ← 串口初始化
│  ├─ stm32f4xx_it.c      ← 中断处理
│  ├─ gpio.c              ← GPIO
│  └─ ...
├─ Drivers/STM32F4xx_HAL_Driver  ← ST 官方库
└─ User                  ← 你自己写的核心代码
   ├─ config.h           ← 所有参数
   ├─ bsp_bluetooth.c    ← 蓝牙协议
   ├─ driver_comm.c      ← 驱动模块通信
   ├─ bsp_motor.c        ← 电机输出
   ├─ bsp_encoder.c      ← 编码器换算
   ├─ chassis_control.c  ← 麦轮运动学
   ├─ pid.c              ← PID
   ├─ control_mode.c     ← 控制模式
   ├─ route.c            ← 路线
   └─ user_app.c         ← 总入口
```

测试工程多一个 `Test` 组：

```text
Test
├─ test_app.c        ← ASCII 命令解析
├─ debug_algo.c      ← 算法/标定函数
├─ pid.c             ← PID 仿真
├─ driver_comm.c
├─ chassis_control.c
└─ bsp_encoder.c
```

### 怎么打开一个文件
- 在左侧树里双击文件名；
- 或在 `Project` 菜单 → `Open File`；
- 或在代码里按 **F12** 跳到函数定义。

### 怎么找代码
- **Ctrl+F**：搜索当前文件；
- **Ctrl+Shift+F**：全局搜索（部分版本）；
- **F12**：跳到函数/变量定义；
- **Alt+←**：返回上一个位置。

---

## 5. 编译（Build）

1. 确认左上角 Target 是 `MecanumCar`（主工程）或 `MecanumTest`（测试工程）；
2. 点工具栏 **Build** 或按 **F7**；
3. 看底部 Build Output：
   - `0 Error(s), 0 Warning(s)` → 成功；
   - 有 Error → 先看**第一条**错误，双击错误可跳到对应行；
   - Warning 可以先不管，但最好也清零。

### 编译成功后固件在哪里

主工程：
`STM32_Project\CubeMX\MecanumCar\MDK-ARM\MecanumCar\MecanumCar.hex`

测试工程：
`Test_Project\MecanumTest\MDK-ARM\MecanumTest\MecanumTest.hex`

> Keil 烧录时用的是 `.axf`，但 `.hex` 也可以给 ST-Link Utility/其它工具用。

---

## 6. 烧录（Download）

### 6.1 接线

- ST-Link 的 `SWDIO → PA13`、`SWCLK → PA14`、`GND → GND`、`3V3 → 3V3`；
- 开发板要有电（ST-Link 3V3 或单独 5V）；
- 第一次测试建议**只给开发板供电，不接电机电源**。

### 6.2 烧录步骤

1. 点工具栏 **Download** 或按 **F8**；
2. 看底部输出：
   - `Erase Done.`
   - `Programming Done.`
   - `Verify OK.`
   - `Flash Load finished`
3. 看到以上文字才算成功。

### 6.3 如果弹出 ST-LINK Firmware Upgrade

- 这是 Keil 提示升级 ST-Link 固件；
- 点 **Yes / 是**；
- 升级完成后重新点 **Download**。

### 6.4 如果提示 No ST-LINK detected / Erase Failed

| 提示 | 优先检查 |
|---|---|
| No ST-LINK detected | USB 线、驱动、ST-Link 是否插好 |
| Erase Failed | 开发板是否上电、SWDIO/SWCLK/GND 是否接对 |
| Target DLL has been cancelled | 先处理 ST-Link 固件升级弹窗，再重试 |
| Cannot access target | 目标芯片是否被复位按住、BOOT0 是否正常 |

---

## 7. 调试（Debug）

### 7.1 进入调试

1. 先编译成功；
2. 点 **Debug** 或按 **Ctrl+F5**；
3. 进入调试界面后，程序会暂停在 `main()` 开头附近。

### 7.2 常用调试操作

| 操作 | 快捷键 | 作用 |
|---|---|---|
| 运行 | F5 | 全速运行，直到断点 |
| 暂停 | 工具栏 Pause | 暂停当前程序 |
| 单步跳过 | F10 | 执行一行，不进入函数 |
| 单步进入 | F11 | 进入函数内部 |
| 单步跳出 | Shift+F11 | 从当前函数跳出 |
| 复位 | 工具栏 Reset | 复位芯片 |
| 设置断点 | F9 | 在光标行设置/取消断点 |
| 退出调试 | Ctrl+F5 | 回到编辑界面 |

### 7.3 看变量

1. 进入调试；
2. 菜单 `View → Watch Windows → Watch 1`；
3. 在 Watch 窗口输入变量名，例如：
   - `g_mode`
   - `g_target_vx`
   - `g_wheel_target`
   - `g_wheel_actual`
   - `g_accel_v`
4. 单步/运行，观察数值变化。

> 变量必须是**全局变量**或当前作用域可见的变量；局部变量在离开函数后就看不到了。

### 7.4 看内存/寄存器/外设

- `View → Memory Windows → Memory 1`：输入地址看内存；
- `View → Registers Window`：看 CPU 寄存器；
- `Peripherals → System Viewer → USART1/USART2`：看串口寄存器；
- `View → Call Stack Window`：看函数调用栈。

### 7.5 调试建议

- 先在主工程里看 `g_mode`、`g_target_vx`、`g_wheel_target`；
- 如果蓝牙无数据，先在 `Bluetooth_OnRxByte()` 设断点，看是否进入；
- 如果编码器无数据，在 `DriverComm_OnRxByte()` 设断点，看是否收到字符；
- 不要一上来就在中断里长时间暂停，容易错过数据。

---

## 8. 测试工程（MecanumTest）怎么用

测试工程不是用来跑小车的，而是用来**单独验证硬件和算法**。

### 8.1 烧录测试工程

1. 打开 `Test_Project\MecanumTest\MDK-ARM\MecanumTest.uvprojx`；
2. 按 **F7** 编译，确认 `0 Error(s)`；
3. 按 **F8** 烧录，确认 `Erase Done / Programming Done / Verify OK`；
4. 板子复位。

### 8.2 打开串口助手（COM5）

1. 用 USB转串口（CH340）接电脑，设备管理器确认端口（当前是 **COM5**）；
2. 打开串口助手（SSCOM、XCOM、串口调试助手等）；
3. 参数：
   - 波特率 **115200**
   - 数据位 8
   - 停止位 1
   - 校验 None
   - 流控 None
   - 发送结尾 **\r\n**（回车换行）
4. 复位开发板，应看到：
   ```text
   === Mecanum Test / Debug ready ===
   Type help for commands
   ```

### 8.3 常用测试命令与预期

| 输入 | 预期输出/现象 |
|---|---|
| `help` | 打印命令列表 |
| `enc` | 打印四轮 `20ms` 和 `total` 计数 |
| `enczero` | 打印 `enczero ok`，计数归零 |
| `wheel 0 0.3` | A 轮转动；`enc` 的 A 轮计数变化 |
| `car 0.3 0 0` | 四轮前进（如果驱动/电机已接） |
| `stop` | 四轮停 |
| `mecanum 0.3 0 0` | 只打印四轮 m/s，不驱动 |
| `geo 0.3 0 0 130 123.5` | 用自定义轴距/轮距打印四轮 m/s |
| `cpcal 1000` | 打印当前 CPR 和建议 CPR |
| `rot90 0.6 900` | 左转 90° 脉冲，900ms 后自动停 |
| `rotcal 85` | 输入实测 85°，打印建议 90° 时间 |
| `min 0.3` | 四轮低速 1.5s，观察震动/平稳 |
| `sign 0 -1` | 把 A 轮方向符号设为 -1 |
| `sign` | 打印四轮符号表 |
| `ramp 0 0.5 1.0` | 打印加速度时间线 |
| `pidstep 0.8 0 0 100` | PID 阶跃仿真，打印位置/输出 |
| `link` | 打印 `link ok` 并读电压 |

### 8.4 典型操作顺序（第一次）

1. `help` — 确认通信；
2. `enc` — 看编码器是否有数；
3. `enczero` — 清零；
4. `wheel 0 0.3` — 单独转 A 轮，看方向和计数；
5. `wheel 1 0.3` / `wheel 2 0.3` / `wheel 3 0.3` — 检查 B/C/D；
6. `car 0.3 0 0` — 四轮前进；
7. `stop` — 停车；
8. 需要标定时再发 `cpcal` / `rot90` / `rotcal` / `min`。

### 8.5 测试完怎么回到主工程

1. 打开 `STM32_Project\CubeMX\MecanumCar\MDK-ARM\MecanumCar.uvprojx`；
2. 按 **F7** 编译；
3. 按 **F8** 烧录；
4. 板子里就恢复成“蓝牙遥控小车”主固件。

> 记住：测试工程和主工程是两套固件，**不能同时存在**。

---

## 9. 常用快捷键速查

| 快捷键 | 作用 |
|---|---|
| F7 | 编译 |
| F8 | 烧录 |
| Ctrl+F5 | 进入/退出调试 |
| F5 | 运行 |
| F9 | 设置/取消断点 |
| F10 | 单步跳过 |
| F11 | 单步进入 |
| Shift+F11 | 单步跳出 |
| Ctrl+F | 当前文件搜索 |
| F12 | 跳转定义 |
| Alt+← | 返回上一个位置 |
| Alt+F7 | Options for Target（部分版本） |

---

## 10. 常见错误与解决

### 10.1 编译类

| 错误 | 原因 | 解决 |
|---|---|---|
| `Target uses ARM-Compiler 'Default Compiler Version 5' which is not available` | 工程选了 AC5，但电脑只装了 AC6 | `Options for Target → Target → ARM Compiler` 选 **V6.22**；本工程已设 `pCCUsed=V6.22` |
| `cannot open source input file "xxx.h"` | 头文件路径没加 | `Options for Target → C/C++ → Include Paths` 加 `../User` 或 `../Test` |
| `undefined symbol xxx` | `.c` 文件没加入工程 | 右键 Group → Add Existing Files，把对应 `.c` 加进去 |
| `Target not created` | 有错误没解决 | 看 Build Output 第一条 Error |

### 10.2 烧录类

| 错误 | 原因 | 解决 |
|---|---|---|
| `No ST-LINK detected` | USB/驱动/线 | 换 USB 口、重插、装 ST-Link 驱动 |
| `Erase Failed` | 目标没电/SWD 没接好 | 开发板上电，检查 SWDIO/SWCLK/GND |
| `Flash Download failed - Target DLL has been cancelled` | ST-Link 固件升级弹窗被取消 | 重新 F8，弹窗点 Yes 升级 |
| `Cannot access target` | 芯片被复位/BOOT0 异常 | 松开复位键，检查 BOOT0 接地 |

### 10.3 串口/测试类

| 现象 | 原因 | 解决 |
|---|---|---|
| COM5 打不开 | 被别的串口助手占用 | 关闭其它串口助手/软件 |
| 发命令没反应 | 波特率/结尾不对 | 115200、8N1、发送 `\r\n` |
| 回显乱码 | 编码/波特率不对 | 用英文命令；确认 115200 |
| `Unknown command` | 命令拼写错 | 发 `help` 看正确拼写 |
| 编码器全 0 | 编码器线/供电/模块 | 检查 6P 插头、Vcc/GND/A/B |
| 轮子不转 | 驱动电源/命令 | 检查 12V、`car`/`wheel`、最小驱动 |

---

## 11. 安全 checklist（每次上电前）

- [ ] 接线前先断电；
- [ ] 电机轮子先悬空；
- [ ] 驱动模块 12V 电源正负极没接反；
- [ ] STM32 用 3.3V/5V，HC-04 用 3.3V；
- [ ] 所有 GND 共地；
- [ ] 驱动模块 UART 的 5V 不接 STM32；
- [ ] 急停按钮/空格键随时可用；
- [ ] 第一次测试不要直接放地上跑。

---

## 12. 建议学习顺序

1. 先看 `diagrams/keil_ui.svg`，认识界面；
2. 打开主工程，按 F7 编译，确认 0 错误；
3. 按 F8 烧录，确认 Verify OK；
4. 打开测试工程，按 F7/F8，接 COM5，发 `help`；
5. 按 `参数手册.md` 做编码器/旋转/最小驱动标定；
6. 回到主工程，烧录，用上位机联调；
7. 再看 `教学手册.md` 理解原理和代码。

### 6.5 第一次烧录前检查 Flash 算法（很重要）

如果 F8 提示找不到 Flash 算法/无法擦除，按下面检查：

1. 点工具栏 **Options for Target**（魔术棒图标）；
2. 选 **Debug** 标签；
3. 右侧 `Use:` 选 **ST-Link Debugger**；
4. 点旁边的 **Settings**；
5. 选 **Flash Download** 标签；
6. 在 `Programming Algorithm` 里点 **Add**；
7. 选择 **STM32F4xx Flash**（或 STM32F4xx 1MB/512KB Flash，按芯片容量）；
8. 勾选 `Reset and Run`（烧完自动运行）；
9. 点 OK 保存，再按 F8。

> 如果 `Add` 里没有 STM32F4xx Flash，说明 Keil 的 STM32F4 Device Family Pack 没装好；需要先装 F4 支持包。

### 6.6 烧录后没反应？

1. 按一下开发板复位键；
2. 看电源灯是否亮；
3. 看串口是否有开机信息（主工程 COM5 115200 会打印 `Mecanum Car boot v0.1`）；
4. 如果没有任何输出，先检查是否烧的是正确工程（主工程/测试工程）。
