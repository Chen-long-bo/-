#include "main.h"             /* HAL */
#include <string.h>           /* strlen */
#include <stdio.h>            /* sprintf */
#include "test_app.h"         /* 本模块 */
#include "config.h"           /* 参数 */
#include "driver_comm.h"      /* 驱动模块通信 */
#include "chassis_control.h"  /* 麦轮运动学 */
#include "bsp_encoder.h"      /* 编码器 */
#include "debug_algo.h"       /* 调试/标定纯算法 */
#include "pid.h"              /* PID 阶跃仿真 */

extern UART_HandleTypeDef huart2;   /* 驱动模块 */
extern UART_HandleTypeDef huart3;   /* 调试串口 COM5 */

#define CMD_LINE_MAX        96          /* 命令行最大长度 */
#define TEST_ROTATE_MS_90   900.0f      /* 当前固件转90°的默认时间 ms */

static char g_cmd_line[CMD_LINE_MAX];   /* 命令行缓冲 */
static uint8_t g_cmd_len = 0;           /* 已收字节数 */
static volatile uint8_t g_dbg_rx_byte = 0;  /* 调试串口接收字节 */
static volatile uint8_t g_drv_rx_byte = 0;  /* 驱动模块接收字节 */
static uint32_t g_last_loop = 0;        /* 上次循环时刻 */
static uint32_t g_tick = 0;             /* 计数 */
static float g_wheel_sign[4] = {1.0f, 1.0f, 1.0f, 1.0f};   /* 四轮方向符号，+1/-1 */
static uint8_t g_pulse_active = 0;      /* 是否有短脉冲运动 */
static uint32_t g_pulse_end_tick = 0;   /* 短脉冲结束时刻 */

/* ---------- 工具函数 ---------- */

/* 打印字符串到调试串口 */
static void Test_Print(const char *s)
{
    HAL_UART_Transmit(&huart3, (uint8_t *)s, (uint16_t)strlen(s), 100);
}

/* 打印整数 */
static void Test_PrintInt(int32_t v)
{
    char buf[16];
    sprintf(buf, "%ld", (long)v);
    Test_Print(buf);
}

/* 打印浮点数（固定3位小数，避免依赖 %f） */
static void Test_PrintFloat(float v)
{
    int p = (int)(v * 1000.0f);          /* 放大1000倍 */
    int neg = (p < 0) ? 1 : 0;           /* 是否为负 */
    int a = neg ? (-p) : p;              /* 绝对值 */
    int ip = a / 1000;                   /* 整数部分 */
    int fp = a % 1000;                   /* 小数部分 */
    char buf[24];
    if (neg) { Test_Print("-"); }        /* 负号 */
    sprintf(buf, "%d.%03d", ip, fp);     /* 格式化 */
    Test_Print(buf);                     /* 输出 */
}

/* 简单字符串转浮点数，避免依赖库 %f */
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

/* 读取下一个浮点参数；返回剩余字符串指针，失败返回 NULL */
static const char *Test_NextFloat(const char *s, float *out)
{
    while (*s == ' ') { s++; }           /* 跳过空格 */
    if (*s == '\0') { return NULL; }     /* 没有参数 */
    *out = Test_Atof(s);                 /* 解析 */
    while (*s && *s != ' ') { s++; }     /* 跳到下一个空格 */
    return s;
}

/* 发送四轮归一化速度（应用方向符号） */
static void Test_SendCar4(float w[4])
{
    float out[4];
    int i;
    for (i = 0; i < 4; i++) { out[i] = w[i] * g_wheel_sign[i]; }   /* 应用符号 */
    DriverComm_SendCar(out[0], out[1], out[2], out[3]);            /* 发给模块 */
}

/* 启动一段短脉冲运动，到时自动停 */
static void Test_StartPulse(float w[4], uint32_t ms)
{
    Test_SendCar4(w);                    /* 先发速度 */
    g_pulse_active = 1;                  /* 标记脉冲 */
    g_pulse_end_tick = HAL_GetTick() + ms;   /* 结束时刻 */
}

/* 停止短脉冲 */
static void Test_StopPulse(void)
{
    float z[4] = {0, 0, 0, 0};
    Test_SendCar4(z);                    /* 四轮0 */
    g_pulse_active = 0;                  /* 清除标记 */
}

/* ---------- 帮助 ---------- */

static void Test_Help(void)
{
    Test_Print("=== Mecanum Test / Debug ===\r\n");
    Test_Print("help                         - show help\r\n");
    Test_Print("stop                         - stop motors\r\n");
    Test_Print("bat                          - read battery\r\n");
    Test_Print("enc                          - read encoders\r\n");
    Test_Print("enczero                      - zero encoders\r\n");
    Test_Print("car <vx> <vy> <wz>           - drive chassis (m/s, m/s, rad/s)\r\n");
    Test_Print("wheel <0-3> <speed>          - single wheel (-1~1)\r\n");
    Test_Print("mecanum <vx> <vy> <wz>       - print 4 wheel targets (no drive)\r\n");
    Test_Print("geo <vx> <vy> <wz> <wb> <tr> - preview geometry (mm)\r\n");
    Test_Print("cpcal <mm>                   - suggest CPR from current counts\r\n");
    Test_Print("rot90 [speed] [ms]           - rotate left 90 deg pulse\r\n");
    Test_Print("rotcal <measured_deg>        - suggest 90deg time\r\n");
    Test_Print("min <speed>                  - low-speed pulse 1500ms\r\n");
    Test_Print("sign [0-3] [1/-1]            - show/set wheel sign\r\n");
    Test_Print("ramp <v0> <v1> <accel>       - print accel ramp timeline\r\n");
    Test_Print("pidstep <kp> <ki> <kd> <tgt> - PID step simulation\r\n");
    Test_Print("raw <text>                   - send raw text to module\r\n");
    Test_Print("link                         - link self-test\r\n");
}

/* ---------- 基础命令 ---------- */

static void Test_Enc(void)
{
    DriverComm_Data_t *d = DriverComm_GetData();
    int i;
    Test_Print("20ms:");
    for (i = 0; i < 4; i++) { Test_Print(" "); Test_PrintInt(d->encoder_20ms[i]); }
    Test_Print("\r\ntotal:");
    for (i = 0; i < 4; i++) { Test_Print(" "); Test_PrintInt(d->encoder_total[i]); }
    Test_Print("\r\n");
}

static void Test_Bat(void)
{
    DriverComm_Data_t *d = DriverComm_GetData();
    Test_Print("battery_raw="); Test_PrintInt(d->battery_raw); Test_Print(" (approx mV)\r\n");
}

static void Test_Car(const char *arg)
{
    float vx = 0, vy = 0, wz = 0;
    const char *p = Test_NextFloat(arg, &vx);
    p = (p ? Test_NextFloat(p, &vy) : NULL);
    p = (p ? Test_NextFloat(p, &wz) : NULL);
    if (!p) { Test_Print("usage: car <vx> <vy> <wz>\r\n"); return; }
    float wt[4];
    int i;
    Chassis_Inverse(vx, vy, wz, wt);                  /* 麦轮逆解算 */
    for (i = 0; i < 4; i++) { wt[i] /= CFG_MAX_WHEEL_SPEED_M_S; }   /* 归一化 */
    Test_SendCar4(wt);
    Test_Print("car ok\r\n");
}

static void Test_Wheel(const char *arg)
{
    float idxf = 0, spd = 0;
    const char *p = Test_NextFloat(arg, &idxf);
    p = (p ? Test_NextFloat(p, &spd) : NULL);
    if (!p) { Test_Print("usage: wheel <0-3> <speed>\r\n"); return; }
    int idx = (int)idxf;
    float w[4] = {0, 0, 0, 0};
    if (idx < 0 || idx > 3) { Test_Print("idx must be 0-3\r\n"); return; }
    w[idx] = spd;
    Test_SendCar4(w);
    Test_Print("wheel ok\r\n");
}

/* ---------- 算法/标定命令 ---------- */

static void Test_Mecanum(const char *arg)
{
    float vx = 0, vy = 0, wz = 0;
    const char *p = Test_NextFloat(arg, &vx);
    p = (p ? Test_NextFloat(p, &vy) : NULL);
    p = (p ? Test_NextFloat(p, &wz) : NULL);
    if (!p) { Test_Print("usage: mecanum <vx> <vy> <wz>\r\n"); return; }
    float w[4];
    DebugAlgo_Mecanum(vx, vy, wz, CFG_WHEELBASE_MM, CFG_TRACK_MM, w);
    Test_Print("wheel m/s: A="); Test_PrintFloat(w[0]);
    Test_Print(" B="); Test_PrintFloat(w[1]);
    Test_Print(" C="); Test_PrintFloat(w[2]);
    Test_Print(" D="); Test_PrintFloat(w[3]);
    Test_Print("\r\n");
}

static void Test_Geo(const char *arg)
{
    float vx = 0, vy = 0, wz = 0, wb = 0, tr = 0;
    const char *p = Test_NextFloat(arg, &vx);
    p = (p ? Test_NextFloat(p, &vy) : NULL);
    p = (p ? Test_NextFloat(p, &wz) : NULL);
    p = (p ? Test_NextFloat(p, &wb) : NULL);
    p = (p ? Test_NextFloat(p, &tr) : NULL);
    if (!p) { Test_Print("usage: geo <vx> <vy> <wz> <wheelbase_mm> <track_mm>\r\n"); return; }
    float w[4];
    DebugAlgo_Mecanum(vx, vy, wz, wb, tr, w);
    Test_Print("geo wheel m/s: A="); Test_PrintFloat(w[0]);
    Test_Print(" B="); Test_PrintFloat(w[1]);
    Test_Print(" C="); Test_PrintFloat(w[2]);
    Test_Print(" D="); Test_PrintFloat(w[3]);
    Test_Print("\r\n");
}

static void Test_Cpcal(const char *arg)
{
    float mm = 0;
    if (!Test_NextFloat(arg, &mm) || mm <= 0.1f) { Test_Print("usage: cpcal <distance_mm>\r\n"); return; }
    int32_t c[4];
    Encoder_GetCounts(c);                    /* 相对累计计数 */
    float avg = (c[0] + c[1] + c[2] + c[3]) / 4.0f;
    if (avg < 0) { avg = -avg; }             /* 取正 */
    float suggested = DebugAlgo_SuggestCpr((int32_t)avg, mm, CFG_WHEEL_DIAMETER_MM);
    Test_Print("current CPR="); Test_PrintFloat(CFG_ENCODER_CPR);
    Test_Print(" suggested CPR="); Test_PrintFloat(suggested);
    Test_Print("\r\n");
}

static void Test_Rot90(const char *arg)
{
    float speed = 0.60f, ms = TEST_ROTATE_MS_90;
    const char *p = Test_NextFloat(arg, &speed);
    if (p) { Test_NextFloat(p, &ms); }
    float w[4] = {-speed, speed, -speed, speed};   /* 左转；speed 为负则右转 */
    Test_StartPulse(w, (uint32_t)ms);
    Test_Print("rot90 start\r\n");
}

static void Test_Rotcal(const char *arg)
{
    float deg = 0;
    if (!Test_NextFloat(arg, &deg) || deg <= 0.1f) { Test_Print("usage: rotcal <measured_deg>\r\n"); return; }
    float suggested = DebugAlgo_SuggestRotateMs(TEST_ROTATE_MS_90, deg);
    Test_Print("current 90deg ms="); Test_PrintFloat(TEST_ROTATE_MS_90);
    Test_Print(" suggested ms="); Test_PrintFloat(suggested);
    Test_Print("\r\n");
}

static void Test_Min(const char *arg)
{
    float spd = 0;
    if (!Test_NextFloat(arg, &spd)) { Test_Print("usage: min <speed>\r\n"); return; }
    float w[4] = {spd, spd, spd, spd};
    Test_StartPulse(w, 1500);
    Test_Print("min pulse 1500ms\r\n");
}

static void Test_Sign(const char *arg)
{
    float idxf = 0, signf = 0;
    const char *p = Test_NextFloat(arg, &idxf);
    if (p) {
        p = Test_NextFloat(p, &signf);
        int idx = (int)idxf;
        if (idx >= 0 && idx <= 3) {
            g_wheel_sign[idx] = (signf >= 0.0f) ? 1.0f : -1.0f;
        }
    }
    Test_Print("sign A="); Test_PrintFloat(g_wheel_sign[0]);
    Test_Print(" B="); Test_PrintFloat(g_wheel_sign[1]);
    Test_Print(" C="); Test_PrintFloat(g_wheel_sign[2]);
    Test_Print(" D="); Test_PrintFloat(g_wheel_sign[3]);
    Test_Print("\r\n");
}

static void Test_Ramp(const char *arg)
{
    float v0 = 0, v1 = 0, accel = 0;
    const char *p = Test_NextFloat(arg, &v0);
    p = (p ? Test_NextFloat(p, &v1) : NULL);
    p = (p ? Test_NextFloat(p, &accel) : NULL);
    if (!p || accel <= 0.0f) { Test_Print("usage: ramp <v0> <v1> <accel>\r\n"); return; }
    float v = v0;
    int i;
    for (i = 0; i < 100; i++) {              /* 2s，20ms一步 */
        v = DebugAlgo_RampStep(v, v1, accel, 0.02f);
        if ((i % 5) == 0) {
            Test_Print("t="); Test_PrintInt(i * 20);
            Test_Print("ms v="); Test_PrintFloat(v);
            Test_Print("\r\n");
        }
        if (v == v1) { break; }
    }
}

static void Test_PidStep(const char *arg)
{
    float kp = 0, ki = 0, kd = 0, target = 0;
    const char *p = Test_NextFloat(arg, &kp);
    p = (p ? Test_NextFloat(p, &ki) : NULL);
    p = (p ? Test_NextFloat(p, &kd) : NULL);
    p = (p ? Test_NextFloat(p, &target) : NULL);
    if (!p) { Test_Print("usage: pidstep <kp> <ki> <kd> <target>\r\n"); return; }
    PID_HandleTypeDef pid;
    PID_Init(&pid, kp, ki, kd, -100.0f, 100.0f);
    float actual = 0.0f;
    int i;
    Test_Print("PID step simulation (mm, 20ms):\r\n");
    for (i = 0; i < 100; i++) {
        float out = PID_Compute(&pid, target, actual, 0.02f);
        actual += out * 0.02f;
        if ((i % 10) == 0) {
            Test_Print("t="); Test_PrintInt(i * 20);
            Test_Print("ms pos="); Test_PrintFloat(actual);
            Test_Print(" out="); Test_PrintFloat(out);
            Test_Print("\r\n");
        }
    }
}

static void Test_Link(void)
{
    Test_Print("link ok (ASCII command received)\r\n");
    DriverComm_RequestBattery();
    Test_Bat();
}

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
    else if (strncmp(line, "stop", 4) == 0) { Test_StopPulse(); Test_Print("stop ok\r\n"); }
    else if (strncmp(line, "bat", 3) == 0) { DriverComm_RequestBattery(); Test_Bat(); }
    else if (strncmp(line, "enczero", 7) == 0) { Encoder_SetZero(); Test_Print("enczero ok\r\n"); }
    else if (strncmp(line, "enc", 3) == 0) { Test_Enc(); }
    else if (strncmp(line, "car ", 4) == 0) { Test_Car(line + 4); }
    else if (strncmp(line, "wheel ", 6) == 0) { Test_Wheel(line + 6); }
    else if (strncmp(line, "mecanum ", 8) == 0) { Test_Mecanum(line + 8); }
    else if (strncmp(line, "geo ", 4) == 0) { Test_Geo(line + 4); }
    else if (strncmp(line, "cpcal ", 6) == 0) { Test_Cpcal(line + 6); }
    else if (strncmp(line, "rot90", 5) == 0) { Test_Rot90(line + 5); }
    else if (strncmp(line, "rotcal ", 7) == 0) { Test_Rotcal(line + 7); }
    else if (strncmp(line, "min ", 4) == 0) { Test_Min(line + 4); }
    else if (strncmp(line, "sign", 4) == 0) { Test_Sign(line + 4); }
    else if (strncmp(line, "ramp ", 5) == 0) { Test_Ramp(line + 5); }
    else if (strncmp(line, "pidstep ", 8) == 0) { Test_PidStep(line + 8); }
    else if (strncmp(line, "raw ", 4) == 0) { Test_Raw(line + 4); }
    else if (strncmp(line, "link", 4) == 0) { Test_Link(); }
    else { Test_Print("Unknown command, type help\r\n"); }
}

/* 收到调试串口一个字节 */
void Test_OnRxByte(uint8_t byte)
{
    if (byte == '\n' || byte == '\r') {
        if (g_cmd_len > 0) {
            g_cmd_line[g_cmd_len] = '\0';
            Test_Print("\r\n");
            Test_Parse(g_cmd_line);
            g_cmd_len = 0;
        }
    }
    else if (g_cmd_len < CMD_LINE_MAX - 1) {
        g_cmd_line[g_cmd_len++] = (char)byte;
    }
}

/* 初始化 */
void Test_Init(void)
{
    DriverComm_Init();
    DriverComm_SetMotorType520();
    DriverComm_SetMotorParam((uint8_t)(CFG_WHEEL_DIAMETER_MM / 10.0f), 11, 56);
    Encoder_Init();

    HAL_UART_Receive_IT(&huart2, (uint8_t *)&g_drv_rx_byte, 1);
    HAL_UART_Receive_IT(&huart3, (uint8_t *)&g_dbg_rx_byte, 1);

    Test_Print("\r\n=== Mecanum Test / Debug ready ===\r\nType help for commands\r\n");
    g_last_loop = HAL_GetTick();
}

/* 主循环：周期请求编码器/电压；处理短脉冲停止 */
void Test_Loop(void)
{
    uint32_t now = HAL_GetTick();

    if ((now - g_last_loop) >= 20) {
        g_last_loop = now;
        g_tick++;
        DriverComm_RequestEncoder20ms();
        if ((g_tick % 5) == 0) { DriverComm_RequestEncoderTotal(); }
        if ((g_tick % 50) == 0) { DriverComm_RequestBattery(); }
    }

    if (g_pulse_active && ((int32_t)(now - g_pulse_end_tick) >= 0)) {
        Test_StopPulse();
        Test_Print("pulse done\r\n");
    }
}

/* UART接收回调 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART2) {
        DriverComm_OnRxByte((uint8_t)g_drv_rx_byte);
        HAL_UART_Receive_IT(&huart2, (uint8_t *)&g_drv_rx_byte, 1);
    }
    else if (huart->Instance == USART3) {
        Test_OnRxByte((uint8_t)g_dbg_rx_byte);
        HAL_UART_Receive_IT(&huart3, (uint8_t *)&g_dbg_rx_byte, 1);
    }
}
