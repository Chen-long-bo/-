#include "debug_algo.h"     /* 本模块头文件 */
#define PI_F 3.14159265f    /* 圆周率常量 */

/* 麦轮逆运动学：车体速度 -> 四轮线速度（m/s）
 * vx 前后、vy 左右、wz 旋转；wheelbase/track 单位 mm。 */
void DebugAlgo_Mecanum(float vx, float vy, float wz,
                       float wheelbase_mm, float track_mm,
                       float wheel_mps[4])
{
    float a = wheelbase_mm / 2000.0f;   /* 半轴距 m */
    float b = track_mm / 2000.0f;       /* 半轮距 m */
    float lw = a + b;                   /* 几何参数 a+b */

    wheel_mps[0] = vx - vy - lw * wz;   /* 左前 */
    wheel_mps[1] = vx + vy + lw * wz;   /* 右前 */
    wheel_mps[2] = vx + vy - lw * wz;   /* 左后 */
    wheel_mps[3] = vx - vy + lw * wz;   /* 右后 */
}

/* 编码器计数 -> 行驶距离（m） */
float DebugAlgo_CountsToDistance(int32_t counts, float cpr, float wheel_dia_mm)
{
    float rev = (float)counts / cpr;                         /* 圈数 */
    return rev * PI_F * (wheel_dia_mm / 1000.0f);            /* 圈数 * 周长 */
}

/* 根据“平均计数 + 实际距离”反算 CPR（counts/输出转） */
float DebugAlgo_SuggestCpr(int32_t counts_avg, float distance_mm, float wheel_dia_mm)
{
    float distance_m = distance_mm / 1000.0f;                /* mm -> m */
    float circumference = PI_F * (wheel_dia_mm / 1000.0f);   /* 轮周长 m */
    float rev = distance_m / circumference;                  /* 输出轴转数 */
    if (rev < 0.0001f) { return 0.0f; }                      /* 距离太小 */
    return (float)counts_avg / rev;                          /* 建议 CPR */
}

/* 根据实测角度反算“转90°所需时间”
 * 当前时间 current_ms_per_90 对应 90°；实测转了 measured_deg 度，
 * 则转 90° 所需时间 = current * 90 / measured。 */
float DebugAlgo_SuggestRotateMs(float current_ms_per_90, float measured_deg)
{
    if (measured_deg < 0.1f) { return current_ms_per_90; }   /* 角度太小，保持原值 */
    return current_ms_per_90 * 90.0f / measured_deg;         /* 按比例换算 */
}

/* 加速度平滑一步：把 current 按 accel*dt 逼近 target */
float DebugAlgo_RampStep(float current, float target, float accel, float dt)
{
    float step = accel * dt;                                 /* 本周期的速度增量 */
    if (target > current) {                                  /* 加速 */
        current += step;
        if (current > target) { current = target; }
    } else if (target < current) {                           /* 减速 */
        current -= step;
        if (current < target) { current = target; }
    }
    return current;
}
