#ifndef __PID_H
#define __PID_H

/* PID控制器结构体：每个控制环用一个实例 */
typedef struct
{
    float kp;          /* 比例系数 */
    float ki;          /* 积分系数 */
    float kd;          /* 微分系数 */
    float out_max;     /* 输出上限，防止输出过大 */
    float out_min;     /* 输出下限 */
    float integral;    /* 积分累加值 */
    float prev_error;  /* 上一次误差，用于微分项 */
} PID_HandleTypeDef;

void PID_Init(PID_HandleTypeDef *pid, float kp, float ki, float kd, float out_min, float out_max); /* 初始化PID */
void PID_SetParam(PID_HandleTypeDef *pid, float kp, float ki, float kd);                            /* 在线修改PID参数 */
void PID_Reset(PID_HandleTypeDef *pid);                                                             /* 清空积分和上次误差 */
float PID_Compute(PID_HandleTypeDef *pid, float target, float actual, float dt);                    /* 计算一次PID输出 */

#endif /* __PID_H */
