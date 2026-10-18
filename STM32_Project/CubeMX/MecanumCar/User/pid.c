#include "pid.h"   /* 包含本模块头文件 */

/* 初始化PID：设置参数和输出限幅，并清零内部状态 */
void PID_Init(PID_HandleTypeDef *pid, float kp, float ki, float kd, float out_min, float out_max)
{
    pid->kp = kp;              /* 保存比例系数 */
    pid->ki = ki;              /* 保存积分系数 */
    pid->kd = kd;              /* 保存微分系数 */
    pid->out_min = out_min;    /* 保存输出下限 */
    pid->out_max = out_max;    /* 保存输出上限 */
    PID_Reset(pid);            /* 清空积分和上次误差 */
}

/* 在线修改PID参数：只改系数，不破坏当前控制状态 */
void PID_SetParam(PID_HandleTypeDef *pid, float kp, float ki, float kd)
{
    pid->kp = kp;              /* 更新比例系数 */
    pid->ki = ki;              /* 更新积分系数 */
    pid->kd = kd;              /* 更新微分系数 */
}

/* 复位PID内部状态：清空积分和上次误差 */
void PID_Reset(PID_HandleTypeDef *pid)
{
    pid->integral = 0.0f;      /* 积分清零 */
    pid->prev_error = 0.0f;    /* 上次误差清零 */
}

/* 计算一次位置式PID输出，dt为两次调用间隔（秒） */
float PID_Compute(PID_HandleTypeDef *pid, float target, float actual, float dt)
{
    float error;    /* 本次误差 */
    float p_out;    /* 比例项输出 */
    float i_out;    /* 积分项输出 */
    float d_out;    /* 微分项输出 */
    float output;   /* 最终输出 */

    error = target - actual;                        /* 计算误差 = 目标值 - 实际值 */
    pid->integral += error * dt;                    /* 误差积分累加，用于消除稳态误差 */

    /* 积分限幅：防止积分饱和导致超调过大 */
    if (pid->integral > pid->out_max) { pid->integral = pid->out_max; }   /* 积分超过上限时钳位 */
    if (pid->integral < pid->out_min) { pid->integral = pid->out_min; }   /* 积分低于下限时钳位 */

    p_out = pid->kp * error;                        /* 比例项 = kp * 误差 */
    i_out = pid->ki * pid->integral;                /* 积分项 = ki * 积分 */
    d_out = pid->kd * (error - pid->prev_error);    /* 微分项 = kd * 误差变化量，dt已并入kd或由调用方保证 */

    output = p_out + i_out + d_out;                 /* 三项相加得到总输出 */
    pid->prev_error = error;                        /* 保存本次误差，供下次微分使用 */

    /* 输出限幅：保证最终输出在允许范围内 */
    if (output > pid->out_max) { output = pid->out_max; }   /* 输出上限钳位 */
    if (output < pid->out_min) { output = pid->out_min; }   /* 输出下限钳位 */

    return output;                                  /* 返回PID输出 */
}
