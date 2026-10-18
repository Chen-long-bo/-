#include "chassis_control.h"   /* 包含本模块头文件 */
#include "config.h"            /* 读取车轮和底盘尺寸参数 */

/* 底盘初始化：目前没有额外硬件要初始化，先留空 */
void Chassis_Init(void)
{
    /* 以后如果需要在底盘层做初始化（例如传感器），写在这里 */
}

/* 麦克纳姆轮逆运动学：把车体速度换算成四个轮子的线速度（米/秒）
 * 输入：
 *   vx = 车体前后速度，正为前进，单位：米/秒
 *   vy = 车体左右速度，正为向左，单位：米/秒
 *   wz = 车体旋转角速度，正为逆时针，单位：弧度/秒
 * 输出：
 *   wheel_mps[0]=左前轮，[1]=右前轮，[2]=左后轮，[3]=右后轮
 */
void Chassis_Inverse(float vx, float vy, float wz, float wheel_mps[4])
{
    float a = CFG_WHEELBASE_MM / 2000.0f;   /* 半轴距：前后轴距/2，换算成米 */
    float b = CFG_TRACK_MM / 2000.0f;       /* 半轮距：左右轮距/2，换算成米 */
    float lw = a + b;                       /* 麦轮解算用的几何参数 a+b */

    wheel_mps[0] = vx - vy - lw * wz;       /* 左前轮线速度 */
    wheel_mps[1] = vx + vy + lw * wz;       /* 右前轮线速度 */
    wheel_mps[2] = vx + vy - lw * wz;       /* 左后轮线速度 */
    wheel_mps[3] = vx - vy + lw * wz;       /* 右后轮线速度 */

    /* 注意：如果实车前进/左右/旋转方向反了，先量轮距轴距，再回 config.h 或本函数改符号 */
}

/* 麦克纳姆轮正运动学：由四轮线速度反推车体速度，主要用于调试检查 */
void Chassis_Forward(float wheel_mps[4], float *vx, float *vy, float *wz)
{
    float a = CFG_WHEELBASE_MM / 2000.0f;   /* 半轴距，单位：米 */
    float b = CFG_TRACK_MM / 2000.0f;       /* 半轮距，单位：米 */
    float lw = a + b;                       /* 几何参数 a+b */

    *vx = (wheel_mps[0] + wheel_mps[1] + wheel_mps[2] + wheel_mps[3]) / 4.0f;      /* 前后速度平均 */
    *vy = (-wheel_mps[0] + wheel_mps[1] + wheel_mps[2] - wheel_mps[3]) / 4.0f;     /* 左右速度解算 */
    *wz = (-wheel_mps[0] + wheel_mps[1] - wheel_mps[2] + wheel_mps[3]) / (4.0f * lw); /* 旋转角速度解算 */
}
