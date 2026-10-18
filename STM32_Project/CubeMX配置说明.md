# CubeMX 配置说明（第2步）

> 目标：用 STM32CubeMX 生成 Keil5(MDK) 工程，然后把 `User` 文件夹加入工程，编译出能运行的下位机程序。

## 一、CubeMX 新建工程

1. 打开 STM32CubeMX，点 `File → New Project`。
2. 在芯片搜索框输入 `STM32F407VET6`，选中后点 `Start Project`。

## 二、配置引脚与外设

### 1. SYS（调试口）
- 左侧 `System Core → SYS`
- `Debug` 选 `Serial Wire`（保留 SWD 下载，即 PA13/PA14）

### 2. RCC（时钟）
- `System Core → RCC`
- `High Speed Clock (HSE)` 选 `Crystal/Ceramic Resonator`（板上有 8MHz 晶振）

### 3. 三个串口

| 串口 | 用途 | 引脚 | 波特率 |
|---|---|---|---|
| USART1 | HC-04 蓝牙 | PA9=TX, PA10=RX | 9600, 8N1 |
| USART2 | 四路驱动模块 | PA2=TX, PA3=RX | 115200, 8N1 |
| USART3 | USB转串口调试 | PB10=TX, PB11=RX | 115200, 8N1 |

操作：
- `Connectivity → USART1`，`Mode` 选 `Asynchronous`；波特率 9600，其它默认（8N1）。
- `Connectivity → USART2`，`Mode` 选 `Asynchronous`；波特率 115200。
- `Connectivity → USART3`，`Mode` 选 `Asynchronous`；波特率 115200。
- 引脚若和默认不同，在右侧芯片图上手动把 TX/RX 拖到上面表格的引脚。

### 4. 使能串口接收中断（重要）

- `System Core → NVIC`
- 勾选 `USART1 global interrupt` 和 `USART2 global interrupt`。
- USART3 只用来发调试信息，不勾中断也没关系。

## 三、配置时钟到 168MHz

1. 点 `Clock Configuration`。
2. `HSE` 输入 8MHz。
3. `PLL Source HSE`，`PLLM=8`、`PLLN=336`、`PLLP=2`。
4. 让 `SYSCLK=168MHz`，`APB1=42MHz`，`APB2=84MHz`。
5. 有红色报错就按提示把分频改对。

## 四、生成 Keil 工程

1. 点 `Project Manager`。
2. `Project Name` 填 `MecanumCar`，`Project Location` 选一个你自己好找的文件夹。
3. `Toolchain / IDE` 选 `MDK-ARM V5`。
4. 点右上角 `GENERATE CODE` 生成工程。

## 五、把 User 文件夹加进 Keil

1. 把本目录下的 `User` 整个文件夹复制到 CubeMX 生成的工程根目录（和 `Core`、`Drivers` 平级）。
2. 用 Keil5 打开生成的 `.uvprojx`。
3. 右键工程名 → `Add Group...`，新建一个组，名字叫 `User`。
4. 右键 `User` 组 → `Add Existing Files...`，把 `User` 文件夹里的所有 `.c` 文件加进去（`.h` 不用加）。
5. 点魔术棒 `Options for Target`：
   - `C/C++` 标签 → `Include Paths`，点 `...`，把 `User` 文件夹的绝对路径加进去。
   - `C/C++` 标签 → `C99 Mode` 勾上（如果 Keil 是 AC5 编译器）。
   - `Target` 标签里确认芯片是 STM32F407VE。

## 六、修改 main.c（三处）

1. 顶部 include 区加：
```c
#include "user_app.h"
```

2. 在 `main()` 里，`MX_XXX_Init()` 那一串外设初始化**之后**、`while(1)` 之前加：
```c
User_Init();
```

3. 把 `while(1)` 里的 `MX_...` 保留，在循环里加：
```c
while (1)
{
    User_Loop();
}
```

## 七、编译与下载

1. 点 Keil 的 `Build (F7)`。
2. 若有报错，把报错信息发我，我来改。
3. 编译通过后用 ST-Link 下载：`Flash → Download (F8)`。

## 八、上电自检

1. 打开串口助手，选 **COM5（USB转串口）**，波特率 115200。
2. 复位开发板，应该能看到：`Mecanum Car boot v0.1`。
3. 看到这行字，说明第2步成功。
