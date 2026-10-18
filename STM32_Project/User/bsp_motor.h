#ifndef __BSP_MOTOR_H
#define __BSP_MOTOR_H

/* 电机抽象层：向驱动模块发送闭环转速指令 */
void Motor_Init(void);                          /* 初始化电机类型和参数 */
void Motor_SetSpeed(float speed[4]);            /* 设置四轮转速，范围-1~1（$Car闭环） */
void Motor_Stop(void);                          /* 四轮转速归0 */

#endif
