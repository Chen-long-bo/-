#ifndef __CONTROL_MODE_H
#define __CONTROL_MODE_H

#include <stdint.h>

/* 小车运行模式 */
typedef enum
{
    MODE_IDLE = 0,      /* 空闲 */
    MODE_MANUAL = 1,    /* 手动遥控 */
    MODE_BRAKE_SOFT = 2,/* 缓停 */
    MODE_POS_STOP = 3,  /* PID精准停（位置环，速度环由模块$Car完成） */
    MODE_ROUTE = 4,     /* 固定路线 */
    MODE_ROTATE_ANGLE = 5   /* 原地旋转指定角度 */
} ControlMode_t;

void ControlMode_Init(void);                                          /* 初始化 */
void ControlMode_OnCommand(uint8_t cmd, const uint8_t *data, uint8_t len); /* 处理上位机指令 */
void ControlMode_Poll(void);                                          /* 主循环 */

#endif

