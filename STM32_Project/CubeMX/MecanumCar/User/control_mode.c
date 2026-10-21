#include "main.h"             /* HAL */
#include <string.h>           /* memset */
#include <math.h>             /* fabsf */
#include "config.h"           /* 参数 */
#include "pid.h"              /* 位置环PID */
#include "chassis_control.h"  /* 麦轮运动学 */
#include "bsp_motor.h"        /* 电机输出 */
#include "bsp_encoder.h"      /* 编码器反馈 */
#include "driver_comm.h"      /* 电池电压 */
#include "bsp_bluetooth.h"    /* 状态上报 */
#include "route.h"            /* 固定路线 */
#include "control_mode.h"     /* 本模块 */

#define POS_STOP_TOL_MM    10.0f   /* 位置PID到位误差 mm */

static ControlMode_t g_mode = MODE_IDLE;        /* 当前模式 */
static float g_target_vx = 0.0f;                /* 目标前后速度 m/s */
static float g_target_vy = 0.0f;                /* 目标左右速度 m/s */
static float g_target_wz = 0.0f;                /* 目标旋转 rad/s */
static float g_max_speed = CFG_MAX_SPEED_M_S;   /* 最大线速度 */
static float g_max_omega = CFG_MAX_OMEGA_RAD_S; /* 最大角速度 */
static PID_HandleTypeDef g_pos_pid;             /* 位置环PID */
static float g_wheel_target[4] = {0,0,0,0};     /* 四轮目标转速 -1~1 */
static float g_wheel_actual[4] = {0,0,0,0};     /* 四轮实际线速度 m/s */
static float g_pos_start = 0.0f;                /* PID位置控制起点 m */
static float g_pos_target = 0.0f;               /* PID目标相对距离 m */
static uint32_t g_rotate_end_tick = 0;          /* 旋转结束时刻 */
static float g_rotate_dir = 1.0f;               /* 旋转方向：+1左转，-1右转 */
static uint32_t g_last_tick = 0;                /* 上次控制时刻 */
static uint32_t g_last_tele = 0;                /* 上次上报时刻 */
static uint32_t g_tick_count = 0;               /* 周期计数 */

/* ---------- 小端读写辅助 ---------- */
static int16_t ReadInt16(const uint8_t *p)
{ return (int16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8)); }

static uint16_t ReadUInt16(const uint8_t *p)
{ return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8)); }

static void WriteUInt16(uint8_t *p, uint16_t v)
{ p[0] = (uint8_t)(v & 0xFF); p[1] = (uint8_t)((v >> 8) & 0xFF); }

static void WriteInt16(uint8_t *p, int16_t v)
{ WriteUInt16(p, (uint16_t)v); }

static void WriteInt32(uint8_t *p, int32_t v)
{
    uint32_t u = (uint32_t)v;
    p[0] = (uint8_t)(u & 0xFF);
    p[1] = (uint8_t)((u >> 8) & 0xFF);
    p[2] = (uint8_t)((u >> 16) & 0xFF);
    p[3] = (uint8_t)((u >> 24) & 0xFF);
}

static float Clamp(float v, float lo, float hi)
{ if (v > hi) return hi; if (v < lo) return lo; return v; }

/* 当前四轮平均行驶距离，单位 m */
static float ControlMode_GetDistance(void)
{
    int32_t c[4];
    float d = 0.0f;
    int i;
    Encoder_GetCounts(c);
    for (i = 0; i < 4; i++) { d += Encoder_CountsToDistance(c[i]); }
    return d / 4.0f;
}

/* 执行一次速度指令：车体速度 -> 麦轮解算 -> 归一化 -> $Car */
static void ControlMode_RunSpeedLoop(float vx, float vy, float wz, uint8_t apply_min)
{
    float wt[4];
    int i;

    Chassis_Inverse(vx, vy, wz, wt);            /* 麦轮逆解算 */
    for (i = 0; i < 4; i++) {
        g_wheel_target[i] = Clamp(wt[i] / CFG_MAX_WHEEL_SPEED_M_S, -1.0f, 1.0f);
    }
    if (apply_min) {
        float maxw = 0.0f;
        for (i = 0; i < 4; i++) {
            float a = fabsf(g_wheel_target[i]);
            if (a > maxw) { maxw = a; }
        }
        if (maxw > 0.001f && maxw < CFG_MIN_DRIVE) {
            float s = CFG_MIN_DRIVE / maxw;
            for (i = 0; i < 4; i++) { g_wheel_target[i] *= s; }
        }
    }
    Motor_SetSpeed(g_wheel_target);             /* 发送四轮目标速度 */
    Encoder_GetWheelSpeeds(g_wheel_actual);     /* 读取实际速度用于遥测 */
}

/* 初始化 */
void ControlMode_Init(void)
{
    PID_Init(&g_pos_pid, CFG_POS_KP, CFG_POS_KI, CFG_POS_KD,
             -CFG_MAX_SPEED_M_S, CFG_MAX_SPEED_M_S);
    g_mode = MODE_IDLE;
    g_target_vx = g_target_vy = g_target_wz = 0.0f;
    g_pos_start = g_pos_target = 0.0f;
    g_rotate_end_tick = 0;
    g_rotate_dir = 1.0f;
    g_last_tick = HAL_GetTick();
    g_last_tele = g_last_tick;
    g_tick_count = 0;
}

/* 处理上位机指令 */
void ControlMode_OnCommand(uint8_t cmd, const uint8_t *data, uint8_t len)
{
    switch (cmd)
    {
    case 0x01:   /* 手动全向速度 */
        if (len >= 6) {
            g_target_vx = Clamp(ReadInt16(data + 0) / 1000.0f, -g_max_speed, g_max_speed);
            g_target_vy = Clamp(ReadInt16(data + 2) / 1000.0f, -g_max_speed, g_max_speed);
            g_target_wz = Clamp(ReadInt16(data + 4) / 1000.0f, -g_max_omega, g_max_omega);
            g_mode = MODE_MANUAL;
        }
        break;

    case 0x02:   /* 急刹停 */
        Motor_Stop();
        g_target_vx = g_target_vy = g_target_wz = 0.0f;
        g_mode = MODE_IDLE;
        break;

    case 0x04:   /* PID位置控制：目标相对距离，单位mm */
        if (len >= 2) {
            g_pos_start = ControlMode_GetDistance();
            g_pos_target = ReadInt16(data) / 1000.0f;
            PID_Reset(&g_pos_pid);
            g_target_vy = 0.0f;
            g_target_wz = 0.0f;
            g_mode = MODE_POS_STOP;
        }
        break;

    case 0x05:   /* 固定路线占位接口 */
        if (len >= 2) {
            if (data[0] == 0) { Route_Start((uint16_t)data[1] * 100); }
            g_mode = MODE_ROUTE;
        }
        break;

    case 0x06:   /* 急停 */
        Motor_Stop();
        g_target_vx = g_target_vy = g_target_wz = 0.0f;
        g_mode = MODE_IDLE;
        break;

    case 0x07:   /* 预留：速度环在驱动模块内部完成 */
        break;

    case 0x08:   /* 设置位置环PID */
        if (len >= 6) {
            float kp = ReadUInt16(data + 0) / 1000.0f;
            float ki = ReadUInt16(data + 2) / 1000.0f;
            float kd = ReadUInt16(data + 4) / 1000.0f;
            PID_SetParam(&g_pos_pid, kp, ki, kd);
        }
        break;

    case 0x09:   /* 清编码器零点 */
        Encoder_SetZero();
        break;

    case 0x0A:   /* 心跳 */
        {
            uint8_t a[2];
            a[0] = 0x0A;
            a[1] = 0;
            Bluetooth_SendFrame(0x83, a, 2);
        }
        break;

    case 0x0B:   /* 读取参数 */
        {
            uint8_t p[16];
            WriteUInt16(p + 0,  (uint16_t)(g_pos_pid.kp * 1000.0f));
            WriteUInt16(p + 2,  (uint16_t)(g_pos_pid.ki * 1000.0f));
            WriteUInt16(p + 4,  (uint16_t)(g_pos_pid.kd * 1000.0f));
            WriteUInt16(p + 6,  0);
            WriteUInt16(p + 8,  0);
            WriteUInt16(p + 10, 0);
            WriteUInt16(p + 12, (uint16_t)(g_max_speed * 1000.0f));
            WriteUInt16(p + 14, (uint16_t)(g_max_omega * 1000.0f));
            Bluetooth_SendFrame(0x85, p, 16);
        }
        break;

    case 0x0C:   /* 设置限幅 */
        if (len >= 4) {
            g_max_speed = ReadUInt16(data + 0) / 1000.0f;
            g_max_omega = ReadUInt16(data + 2) / 1000.0f;
        }
        break;

    case 0x0D:   /* 原地旋转：角度单位0.1度，正=左转/逆时针 */
        if (len >= 2) {
            float deg = ReadInt16(data) / 10.0f;
            float ms = fabsf(deg) / 90.0f * CFG_ROTATE_MS_PER_90;
            g_rotate_dir = (deg >= 0.0f) ? 1.0f : -1.0f;
            g_rotate_end_tick = HAL_GetTick() + (uint32_t)ms;
            g_mode = MODE_ROTATE_ANGLE;
        }
        break;

    default:
        break;
    }
}

/* 状态上报 */
static void ControlMode_SendStatus(void)
{
    uint8_t buf[32];
    DriverComm_Data_t *d = DriverComm_GetData();
    int32_t enc[4];
    int i;

    Encoder_GetCounts(enc);
    buf[0] = (uint8_t)g_mode;
    WriteUInt16(buf + 1, d->battery_raw);
    for (i = 0; i < 4; i++) { WriteInt32(buf + 3 + i * 4, enc[i]); }
    for (i = 0; i < 4; i++) { WriteInt16(buf + 19 + i * 2, (int16_t)(g_wheel_actual[i] * 1000.0f)); }
    Bluetooth_SendFrame(0x81, buf, 27);
}

/* 曲线数据上报 */
static void ControlMode_SendCurve(void)
{
    uint8_t buf[16];
    int i;
    for (i = 0; i < 4; i++) { WriteInt16(buf + i * 2, (int16_t)(g_wheel_target[i] * 1000.0f)); }
    for (i = 0; i < 4; i++) { WriteInt16(buf + 8 + i * 2, (int16_t)(g_wheel_actual[i] * 1000.0f)); }
    Bluetooth_SendFrame(0x82, buf, 16);
}

/* 主循环 */
void ControlMode_Poll(void)
{
    uint32_t now = HAL_GetTick();

    if ((now - g_last_tick) >= CFG_LOOP_MS) {
        g_last_tick = now;
        g_tick_count++;

        Encoder_Request20ms();
        if ((g_tick_count % 5) == 0) { Encoder_RequestTotal(); }
        if ((g_tick_count % 50) == 0) { DriverComm_RequestBattery(); }

        switch (g_mode)
        {
        case MODE_IDLE:
            Motor_Stop();
            break;

        case MODE_MANUAL:
            ControlMode_RunSpeedLoop(g_target_vx, g_target_vy, g_target_wz, 1);
            break;

        case MODE_POS_STOP:
            {
                float cur = ControlMode_GetDistance();
                float err = (g_pos_start + g_pos_target) - cur;
                float vx = PID_Compute(&g_pos_pid, g_pos_start + g_pos_target, cur,
                                       (float)CFG_LOOP_MS / 1000.0f);
                vx = Clamp(vx, -g_max_speed, g_max_speed);
                if (fabsf(err) < (POS_STOP_TOL_MM / 1000.0f)) {
                    Motor_Stop();
                    g_mode = MODE_IDLE;
                } else {
                    ControlMode_RunSpeedLoop(vx, 0.0f, 0.0f, 0);
                }
            }
            break;

        case MODE_ROTATE_ANGLE:
            if ((int32_t)(HAL_GetTick() - g_rotate_end_tick) >= 0) {
                Motor_Stop();
                g_mode = MODE_IDLE;
            } else {
                float w[4];
                w[0] = -g_rotate_dir * CFG_ROTATE_DRIVE;
                w[1] =  g_rotate_dir * CFG_ROTATE_DRIVE;
                w[2] = w[0];
                w[3] = w[1];
                Motor_SetSpeed(w);
                g_wheel_target[0] = w[0]; g_wheel_target[1] = w[1];
                g_wheel_target[2] = w[2]; g_wheel_target[3] = w[3];
                Encoder_GetWheelSpeeds(g_wheel_actual);
            }
            break;

        case MODE_ROUTE:
            {
                float vx, vy, wz;
                Route_Poll(&vx, &vy, &wz);
                ControlMode_RunSpeedLoop(vx, vy, wz, 1);
            }
            break;

        default:
            Motor_Stop();
            g_mode = MODE_IDLE;
            break;
        }
    }

    if ((now - g_last_tele) >= CFG_TELEMETRY_MS) {
        g_last_tele = now;
        ControlMode_SendStatus();
        ControlMode_SendCurve();
    }
}
