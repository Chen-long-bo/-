#include "main.h"             /* HAL */
#include <string.h>           /* strlen */
#include "user_app.h"         /* 本模块 */
#include "driver_comm.h"      /* 驱动模块 */
#include "bsp_bluetooth.h"    /* 蓝牙/上位机协议 */
#include "bsp_motor.h"        /* 电机 */
#include "bsp_encoder.h"      /* 编码器 */
#include "chassis_control.h"  /* 麦轮 */
#include "control_mode.h"     /* 控制模式 */

extern UART_HandleTypeDef huart1;   /* 蓝牙 */
extern UART_HandleTypeDef huart2;   /* 驱动模块 */
extern UART_HandleTypeDef huart3;   /* 调试/有线联调 */

static volatile uint8_t g_bt_rx_byte = 0;    /* 蓝牙接收字节 */
static volatile uint8_t g_drv_rx_byte = 0;   /* 驱动模块接收字节 */
static volatile uint8_t g_dbg_rx_byte = 0;   /* 调试串口接收字节 */

/* 调试串口发送字符串 */
static void Debug_SendString(const char *str)
{
    HAL_UART_Transmit(&huart3, (uint8_t *)str, (uint16_t)strlen(str), 100);
}

/* 初始化所有模块 */
void User_Init(void)
{
    DriverComm_Init();                                  /* 驱动模块通信 */
    Bluetooth_Init();                                   /* 协议解析 */
    Chassis_Init();                                     /* 运动学 */
    ControlMode_Init();                                 /* 控制模式 */

    HAL_UART_Receive_IT(&huart1, (uint8_t *)&g_bt_rx_byte, 1);    /* 蓝牙接收 */
    HAL_UART_Receive_IT(&huart2, (uint8_t *)&g_drv_rx_byte, 1);   /* 驱动模块接收 */
    HAL_UART_Receive_IT(&huart3, (uint8_t *)&g_dbg_rx_byte, 1);   /* 调试/有线接收 */

    Motor_Init();                                       /* 电机类型/参数 */
    Encoder_Init();                                     /* 编码器零点 */

    Debug_SendString("Mecanum Car boot v0.1\r\n");      /* 开机提示 */
}

/* 主循环 */
void User_Loop(void)
{
    ControlMode_Poll();                                 /* 控制主循环 */
}

/* UART接收完成回调：按串口分发并重新启动接收 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1) {                    /* 蓝牙 */
        Bluetooth_OnRxByte((uint8_t)g_bt_rx_byte);
        HAL_UART_Receive_IT(&huart1, (uint8_t *)&g_bt_rx_byte, 1);
    }
    else if (huart->Instance == USART2) {               /* 驱动模块 */
        DriverComm_OnRxByte((uint8_t)g_drv_rx_byte);
        HAL_UART_Receive_IT(&huart2, (uint8_t *)&g_drv_rx_byte, 1);
    }
    else if (huart->Instance == USART3) {               /* 调试/有线联调 */
        Bluetooth_OnRxByte((uint8_t)g_dbg_rx_byte);
        HAL_UART_Receive_IT(&huart3, (uint8_t *)&g_dbg_rx_byte, 1);
    }
}
