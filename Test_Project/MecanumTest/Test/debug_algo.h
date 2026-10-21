#ifndef __DEBUG_ALGO_H
#define __DEBUG_ALGO_H

#include <stdint.h>

/* 调试/标定用纯算法：不直接操作硬件，方便单独验证 */
void DebugAlgo_Mecanum(float vx, float vy, float wz,
                       float wheelbase_mm, float track_mm,
                       float wheel_mps[4]);                 /* 麦轮逆运动学 */
float DebugAlgo_CountsToDistance(int32_t counts, float cpr, float wheel_dia_mm);   /* 计数->距离 */
float DebugAlgo_SuggestCpr(int32_t counts_avg, float distance_mm, float wheel_dia_mm); /* 距离->建议CPR */
float DebugAlgo_SuggestRotateMs(float current_ms_per_90, float measured_deg);       /* 旋转时间标定 */
#endif
