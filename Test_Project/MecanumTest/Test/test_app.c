#include "main.h"             /* HAL */
#include <string.h>           /* strlen */
#include <stdio.h>            /* sprintf */
#include "test_app.h"         /* 本模块 */
#include "config.h"           /* 参数 */
#include "driver_comm.h"      /* 驱动模块通信 */
#include "chassis_control.h"  /* 麦轮运动学 */
#include "bsp_encoder.h"      /* 编码器 */

extern UART_HandleTypeDef huart2;   /* 驱动模块 */
extern UART_HandleTypeDef huart3;   /* 调试串口 COM5 */

#define CMD_LINE_MAX    64          /* 命令行最大长度 */

static char g_cmd_line[CMD_LINE_MAX];   /* 命令行缓冲 */
static uint8_t g_cmd_len = 0;           /* 已收字节数 */
static volatile uint8_t g_dbg_rx_byte = 0;  /* 调试串口接收字节 */
static volatile uint8_t g_drv_rx_byte = 0;  /* 驱动模块接收字节 */
static uint32_t g_last_loop = 0;        /* 上次循环时刻 */
static uint32_t g_tick = 0;             /* 计数 */

/* ---------- 工具函数 ---------- */

/* 打印字符串到调试串口 */
static void Test_Print(const char *s)
{
    HAL_UART_Transmit(&huart3, (uint8_t *)s, (uint16_t)strlen(s), 100);
}

/* 打印整数（十进制） */
static void Test_PrintInt(int32_t v)
{
    char buf[16];
    sprintf(buf, "%ld", (long)v);
    Test_Print(buf);
}

/* 简单字符串转浮点数，避免依赖库%f */
static float Test_Atof(const char *s)
{
    float val = 0.0f, frac = 0.0f, scale = 1.0f;
    int sign = 1, in_frac = 0;
    if (*s == '-') { sign = -1; s++; }
    else if (*s == '+') { s++; }
    while (*s) {
        if (*s == '.') { in_frac = 1; s++; continue; }
        if (*s < '0' || *s > '9') { break; }
        if (in_frac) { scale *= 10.0f; frac = frac * 10.0f + (float)(*s - '0'); }
        else { val = val * 10.0f + (float)(*s - '0'); }
        s++;
    }
    return (float)sign * (val + frac / scale);
}

/* 发送四轮归一化速度 */
static void Test_SendCar4(float w[4])
{
    DriverComm_SendCar(w[0], w[1], w[2], w[3]);
}

/* ---------- 命令处理 ---------- */

/* 打印帮助 */
static void Test_Help(void)
{
    Test_Print("=== Mecanum Test ===\r\n");
    Test_Print("help                 - show help\r\n");
    Test_Print("stop                 - stop motors\r\n");
    Test_Print("bat                  - read battery\r\n");
    Test_Print("enc                  - read encoders (20ms + total)\r\n");
    Test_Print("enczero              - zero encoders\r\n");
    Test_Print("car <vx> <vy> <wz>   - set velocity (m/s, m/s, rad/s)\r\n");
    Test_Print("wheel <0-3> <speed>  - single wheel speed (-1~1)\r\n");
    Test_Print("raw <text>           - send raw text to module\r\n");
}

/* 读编码器并打印 */
static void Test_Enc(void)
{
    DriverComm_Data_t *d = DriverComm_GetData();
    char buf[80];
    Test_Print("20ms:");
    for (int i = 0; i < 4; i++) { Test_Print(" "); Test_PrintInt(d->encoder_20ms[i]); }
    Test_Print("\r\ntotal:");
    for (int i = 0; i < 4; i++) { Test_Print(" "); Test_PrintInt(d->encoder_total[i]); }
    (void)buf;
    Test_Print("\r\n");
}

/* 读电池电压 */
static void Test_Bat(void)
{
    DriverComm_Data_t *d = DriverComm_GetData();
    Test_Print("battery_raw="); Test_PrintInt(d->battery_raw); Test_Print(" (approx mV)\r\n");
}

/* 麦轮整车速度 */
static void Test_Car(const char *arg)
{
    float vx = Test_Atof(arg);                      /* 第一个参数 */
    const char *p = arg;
    while (*p && *p != ' ') { p++; } while (*p == ' ') { p++; }   /* 跳到第二个参数 */
    float vy = Test_Atof(p);
    while (*p && *p != ' ') { p++; } while (*p == ' ') { p++; }   /* 跳到第三个参数 */
    float wz = Test_Atof(p);
    float wt[4];
    int i;
    Chassis_Inverse(vx, vy, wz, wt);                /* 麦轮逆解算 */
    for (i = 0; i < 4; i++) {
        if (wt[i] > CFG_MAX_WHEEL_SPEED_M_S) { wt[i] = CFG_MAX_WHEEL_SPEED_M_S; }
        if (wt[i] < -CFG_MAX_WHEEL_SPEED_M_S) { wt[i] = -CFG_MAX_WHEEL_SPEED_M_S; }
        wt[i] /= CFG_MAX_WHEEL_SPEED_M_S;           /* 归一化 */
    }
    Test_SendCar4(wt);
    Test_Print("car ok\r\n");
}

/* 单轮速度 */
static void Test_Wheel(const char *arg)
{
    int idx = (int)Test_Atof(arg);
    const char *p = arg;
    while (*p && *p != ' ') { p++; } while (*p == ' ') { p++; }
    float spd = Test_Atof(p);
    float w[4] = {0, 0, 0, 0};
    if (idx < 0 || idx > 3) { Test_Print("idx must be 0-3\r\n"); return; }
    w[idx] = spd;
    Test_SendCar4(w);
    Test_Print("wheel ok\r\n");
}

/* 直接发原始指令 */
static void Test_Raw(const char *arg)
{
    HAL_UART_Transmit(&huart2, (uint8_t *)arg, (uint16_t)strlen(arg), 100);
    HAL_UART_Transmit(&huart2, (uint8_t *)"!", 1, 100);
    Test_Print("raw ok\r\n");
}

/* 解析并执行一条命令 */
static void Test_Parse(const char *line)
{
    if (strncmp(line, "help", 4) == 0) { Test_Help(); }
    else if (strncmp(line, "stop", 4) == 0) { float z[4] = {0,0,0,0}; Test_SendCar4(z); Test_Print("stop ok\r\n"); }
    else if (strncmp(line, "bat", 3) == 0) { DriverComm_RequestBattery(); Test_Bat(); }
    else if (strncmp(line, "enczero", 7) == 0) { Encoder_SetZero(); Test_Print("enczero ok\r\n"); }
    else if (strncmp(line, "enc", 3) == 0) { Test_Enc(); }
    else if (strncmp(line, "car ", 4) == 0) { Test_Car(line + 4); }
    else if (strncmp(line, "wheel ", 6) == 0) { Test_Wheel(line + 6); }
    else if (strncmp(line, "raw ", 4) == 0) { Test_Raw(line + 4); }
    else { Test_Print("Unknown command, type help\r\n"); }
}

/* 收到调试串口一个字节 */
void Test_OnRxByte(uint8_t byte)
{
    if (byte == '\n' || byte == '\r') {          /* 一行结束 */
        if (g_cmd_len > 0) {
            g_cmd_line[g_cmd_len] = '\0';
            Test_Print("\r\n");
            Test_Parse(g_cmd_line);             /* 执行命令 */
            g_cmd_len = 0;
        }
    }
    else if (g_cmd_len < CMD_LINE_MAX - 1) {
        g_cmd_line[g_cmd_len++] = (char)byte;   /* 存入缓冲 */
    }
}

/* 初始化 */
void Test_Init(void)
{
    DriverComm_Init();
    DriverComm_SetMotorType520();
    DriverComm_SetMotorParam((uint8_t)(CFG_WHEEL_DIAMETER_MM / 10.0f), 11, 56);
    Encoder_Init();

    HAL_UART_Receive_IT(&huart2, (uint8_t *)&g_drv_rx_byte, 1);    /* 驱动模块接收 */
    HAL_UART_Receive_IT(&huart3, (uint8_t *)&g_dbg_rx_byte, 1);    /* 调试串口接收 */

    Test_Print("\r\n=== Mecanum Test ready ===\r\nType help for commands\r\n");
    g_last_loop = HAL_GetTick();
}

/* 主循环：周期请求编码器和电压 */
void Test_Loop(void)
{
    uint32_t now = HAL_GetTick();

    if ((now - g_last_loop) >= 20) {
        g_last_loop = now;
        g_tick++;
        DriverComm_RequestEncoder20ms();          /* 每20ms请求一次 */
        if ((g_tick % 5) == 0) { DriverComm_RequestEncoderTotal(); }
        if ((g_tick % 50) == 0) { DriverComm_RequestBattery(); }
    }
}

/* UART接收回调 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART2) {                       /* 驱动模块响应 */
        DriverComm_OnRxByte((uint8_t)g_drv_rx_byte);
        HAL_UART_Receive_IT(&huart2, (uint8_t *)&g_drv_rx_byte, 1);
    }
    else if (huart->Instance == USART3) {                  /* 调试串口命令 */
        Test_OnRxByte((uint8_t)g_dbg_rx_byte);
        HAL_UART_Receive_IT(&huart3, (uint8_t *)&g_dbg_rx_byte, 1);
    }
}
