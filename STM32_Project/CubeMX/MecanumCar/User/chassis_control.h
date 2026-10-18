#ifndef __CHASSIS_CONTROL_H
#define __CHASSIS_CONTROL_H

/* 麦克纳姆轮底盘运动学接口 */
void Chassis_Init(void);                                                            /* 底盘初始化（当前为占位） */
void Chassis_Inverse(float vx, float vy, float wz, float wheel_mps[4]);             /* 正运动学反解：车体速度 -> 四轮线速度 */
void Chassis_Forward(float wheel_mps[4], float *vx, float *vy, float *wz);          /* 正解：四轮线速度 -> 车体速度（调试用） */

#endif /* __CHASSIS_CONTROL_H */
