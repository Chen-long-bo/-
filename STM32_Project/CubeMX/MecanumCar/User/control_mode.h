#ifndef __CONTROL_MODE_H
#define __CONTROL_MODE_H

#include <stdint.h>

/* 小车运行模式；数值2保留不再使用，避免改变已有状态帧编号 */
typedef enum
{
    MODE_IDLE = 0,          /* 空闲 */
    MODE_MANUAL = 1,        /* 手动遥控，直接速度，不使用PID */
    MODE_POS_STOP = 3,      /* PID位置控制，仅“控制与测试”页使用 */
    MODE_ROUTE = 4,         /* 固定路线，直接速度，不使用PID */
    MODE_ROTATE_ANGLE = 5   /* 原地旋转，时间控制，不使用PID */
} ControlMode_t;

void ControlMode_Init(void);                                          /* 初始化 */
void ControlMode_OnCommand(uint8_t cmd, const uint8_t *data, uint8_t len); /* 处理上位机指令 */
void ControlMode_Poll(void);                                          /* 主循环 */

#endif
