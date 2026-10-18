#ifndef __BSP_ENCODER_H
#define __BSP_ENCODER_H

#include <stdint.h>   /* 使用标准整数类型 */

/* 编码器抽象层：从驱动模块读取编码器计数，并换算成距离/速度 */
void Encoder_Init(void);                          /* 初始化，并以当前计数作为零点 */
void Encoder_SetZero(void);                        /* 把当前累计计数记为0点 */
void Encoder_GetCounts(int32_t counts[4]);         /* 读取四轮相对累计计数 */
void Encoder_GetCounts20ms(int16_t counts[4]);     /* 读取四轮最近20ms计数 */
void Encoder_GetWheelSpeeds(float mps[4]);         /* 读取四轮线速度，单位：米/秒 */
void Encoder_Request20ms(void);                    /* 请求一次20ms计数 */
void Encoder_RequestTotal(void);                   /* 请求一次累计计数 */
float Encoder_CountsToDistance(int32_t counts);    /* 把累计计数换算成行驶距离，单位：米 */

#endif /* __BSP_ENCODER_H */
