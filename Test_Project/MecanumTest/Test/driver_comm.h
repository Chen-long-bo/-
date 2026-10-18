#ifndef __DRIVER_COMM_H
#define __DRIVER_COMM_H

#include <stdint.h>

/* 驱动模块最新数据 */
typedef struct
{
    int32_t encoder_total[4];   /* 四轮累计编码器计数 */
    int16_t encoder_20ms[4];    /* 四轮最近20ms编码器计数 */
    uint16_t battery_raw;       /* 电池电压原始值 */
    uint8_t encoder_total_ok;   /* 累计计数已更新标志 */
    uint8_t encoder_20ms_ok;    /* 20ms计数已更新标志 */
} DriverComm_Data_t;

void DriverComm_Init(void);                                             /* 初始化通信 */
void DriverComm_SendCar(float w1, float w2, float w3, float w4);         /* 发送四轮闭环转速 $Car，范围-1~1 */
void DriverComm_SetMotorType520(void);                                  /* 设置电机类型为520 */
void DriverComm_SetMotorParam(uint8_t dia_cm, uint8_t lines, uint8_t ratio); /* 设置轮径/线数/减速比 */
void DriverComm_RequestEncoder20ms(void);                               /* 请求20ms计数 */
void DriverComm_RequestEncoderTotal(void);                              /* 请求累计计数 */
void DriverComm_RequestBattery(void);                                   /* 请求电压 */
void DriverComm_OnRxByte(uint8_t byte);                                 /* 收到字节时调用 */
DriverComm_Data_t *DriverComm_GetData(void);                            /* 获取数据 */

#endif
