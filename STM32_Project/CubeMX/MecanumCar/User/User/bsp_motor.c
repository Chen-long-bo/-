#include "bsp_motor.h"       /* 本模块头文件 */
#include "driver_comm.h"     /* 驱动模块通信 */
#include "config.h"          /* 参数 */

/* 初始化：设置520电机类型和轮径/线数/减速比 */
void Motor_Init(void)
{
    DriverComm_SetMotorType520();                                      /* 520电机 */
    DriverComm_SetMotorParam((uint8_t)(CFG_WHEEL_DIAMETER_MM / 10.0f), /* 轮径cm */
                             (uint8_t)11,                              /* 编码器11线 */
                             (uint8_t)56);                             /* 减速比56 */
}

/* 设置四轮转速，并限幅到-1~1 */
void Motor_SetSpeed(float speed[4])
{
    float w[4];
    int i;

    for (i = 0; i < 4; i++) {                       /* 四轮限幅 */
        if (speed[i] > 1.0f) { w[i] = 1.0f; }
        else if (speed[i] < -1.0f) { w[i] = -1.0f; }
        else { w[i] = speed[i]; }
    }
    DriverComm_SendCar(w[0], w[1], w[2], w[3]);     /* 发送 $Car */
}

/* 四轮转速归0 */
void Motor_Stop(void)
{
    float zero[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    Motor_SetSpeed(zero);
}
