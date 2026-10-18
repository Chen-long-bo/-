#include "route.h"      /* 本模块头文件 */

/* 说明：正方形路线的完整状态机将在第7步实现。
 * 现在先给出接口和占位逻辑，保证整个工程能编译。 */
static uint16_t g_side_mm = 800;   /* 正方形边长，单位毫米 */

/* 启动正方形路线 */
void Route_Start(uint16_t side_mm)
{
    g_side_mm = side_mm;   /* 保存边长 */
}

/* 路线状态机：目前先输出0速度，后续步骤再实现前进/转向 */
void Route_Poll(float *vx, float *vy, float *wz)
{
    (void)g_side_mm;   /* 边长暂存，第7步实现正方形路线时会真正使用 */
    *vx = 0.0f;   /* 目标前后速度为0（占位） */
    *vy = 0.0f;   /* 目标左右速度为0（占位） */
    *wz = 0.0f;   /* 目标旋转速度为0（占位） */
}

