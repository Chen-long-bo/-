#ifndef __ROUTE_H
#define __ROUTE_H

#include <stdint.h>   /* 使用标准整数类型 */

/* 固定路线模块：第一阶段实现正方形路线 */
void Route_Start(uint16_t side_mm);                /* 启动正方形路线，边长单位毫米 */
void Route_Poll(float *vx, float *vy, float *wz);  /* 路线状态机，输出当前目标速度 */

#endif /* __ROUTE_H */
