#include "bsp_encoder.h"     /* 本模块头文件 */
#include "driver_comm.h"     /* 调用驱动模块通信层 */
#include "config.h"          /* 读取轮径和编码器每转计数 */
#define PI_F 3.14159265f   /* 圆周率常量，避免依赖编译器宏 */

static int32_t g_zero[4] = {0, 0, 0, 0};   /* 四轮零点计数，用于相对计数 */

/* 初始化：把当前累计计数记为0点 */
void Encoder_Init(void)
{
    Encoder_SetZero();   /* 设置零点 */
}

/* 把当前累计计数记为0点 */
void Encoder_SetZero(void)
{
    DriverComm_Data_t *d = DriverComm_GetData();   /* 获取驱动模块数据 */
    int i;                                          /* 循环变量 */
    for (i = 0; i < 4; i++) {                       /* 遍历四轮 */
        g_zero[i] = d->encoder_total[i];            /* 保存当前累计计数作为零点 */
    }
}

/* 读取四轮相对累计计数（减去零点） */
void Encoder_GetCounts(int32_t counts[4])
{
    DriverComm_Data_t *d = DriverComm_GetData();   /* 获取驱动模块数据 */
    int i;                                          /* 循环变量 */
    for (i = 0; i < 4; i++) {                       /* 遍历四轮 */
        counts[i] = d->encoder_total[i] - g_zero[i]; /* 相对计数 = 当前累计 - 零点 */
    }
}

/* 读取四轮最近20ms计数 */
void Encoder_GetCounts20ms(int16_t counts[4])
{
    DriverComm_Data_t *d = DriverComm_GetData();   /* 获取驱动模块数据 */
    int i;                                          /* 循环变量 */
    for (i = 0; i < 4; i++) {                       /* 遍历四轮 */
        counts[i] = d->encoder_20ms[i];             /* 直接返回20ms计数 */
    }
}

/* 读取四轮线速度，单位：米/秒 */
void Encoder_GetWheelSpeeds(float mps[4])
{
    int16_t c20[4];   /* 四轮20ms计数 */
    int i;            /* 循环变量 */

    Encoder_GetCounts20ms(c20);   /* 读取20ms计数 */

    /* 速度 = 20ms走过的圈数 * 轮周长 / 20ms周期 */
    for (i = 0; i < 4; i++) {
        mps[i] = (float)c20[i] * PI_F * (CFG_WHEEL_DIAMETER_MM / 1000.0f) / CFG_ENCODER_CPR / 0.02f;   /* 换算成米/秒 */
    }
}

/* 请求一次20ms计数 */
void Encoder_Request20ms(void)
{
    DriverComm_RequestEncoder20ms();   /* 发送请求 */
}

/* 请求一次累计计数 */
void Encoder_RequestTotal(void)
{
    DriverComm_RequestEncoderTotal();   /* 发送请求 */
}

/* 把累计计数换算成行驶距离，单位：米 */
float Encoder_CountsToDistance(int32_t counts)
{
    float rev = (float)counts / CFG_ENCODER_CPR;                          /* 计数换算成圈数 */
    float dist = rev * PI_F * (CFG_WHEEL_DIAMETER_MM / 1000.0f);   /* 圈数换算成距离 */
    return dist;                                                          /* 返回距离 */
}

