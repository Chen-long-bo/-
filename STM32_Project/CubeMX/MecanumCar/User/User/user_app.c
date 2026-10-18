#include "main.h"             /* HAL */
#include <string.h>           /* strlen */
#include "user_app.h"         /* 本模块 */
#include "driver_comm.h"      /* 驱动模块 */
#include "bsp_bluetooth.h"    /* 蓝牙 */
#include "bsp_motor.h"        /* 电机 */
#include "bsp_encoder.h"      /* 编码器 */
#include "chassis_control.h"  /* 麦轮 */
#include "control_mode.h"     /* 控制模式 */

extern UART_HandleTypeDef huart1;   /* 蓝牙 */
extern UART_HandleTypeDef huart2;   /* 驱动模块 */
extern UART_HandleTypeDef huart3;   /* 调试 */

static volatile uint8_t g_bt_rx_byte = 0;    /* 蓝牙接收字节 */
static volatile uint8_t g_drv_rx_byte = 0;   /* 驱动模块接收字节 */

/* 调试串口发送字符串 */
static void Debug_SendString(const char *str)
{
    HAL_UART_Transmit(&huart3, (uint8_t *)str, (uint16_t)strlen(str), 100);
}

/* 初始化所有模块 */
void User_Init(void)
{
    DriverComm_Init();
    Bluetooth_Init();
    Chassis_Init();
    ControlMode_Init();

    HAL_UART_Receive_IT(&huart1, (uint8_t *)&g_bt_rx_byte, 1);
    HAL_UART_Receive_IT(&huart2, (uint8_t *)&g_drv_rx_byte, 1);

    Motor_Init();
    Encoder_Init();

    Debug_SendString("Mecanum Car boot v0.1\r\n");
}

/* 主循环 */
void User_Loop(void)
{
    ControlMode_Poll();
}

/* UART接收回调 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1) {
        Bluetooth_OnRxByte((uint8_t)g_bt_rx_byte);
        HAL_UART_Receive_IT(&huart1, (uint8_t *)&g_bt_rx_byte, 1);
    }
    else if (huart->Instance == USART2) {
        DriverComm_OnRxByte((uint8_t)g_drv_rx_byte);
        HAL_UART_Receive_IT(&huart2, (uint8_t *)&g_drv_rx_byte, 1);
    }
}
