#ifndef __BSP_BLUETOOTH_H
#define __BSP_BLUETOOTH_H

#include <stdint.h>   /* 使用标准整数类型 */

/* 蓝牙通信模块：负责PC<->STM32的协议收发 */
void Bluetooth_Init(void);                                              /* 初始化蓝牙协议解析状态 */
void Bluetooth_OnRxByte(uint8_t byte);                                  /* 收到一个字节时调用（由UART回调调用） */
void Bluetooth_SendFrame(uint8_t cmd, const uint8_t *data, uint8_t len); /* 发送一帧：帧头+长度+指令+数据+校验 */

#endif /* __BSP_BLUETOOTH_H */
