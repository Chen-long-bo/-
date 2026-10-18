#include "main.h"            /* 使用HAL库和UART句柄 */
#include <string.h>          /* 使用memcpy复制数据 */
#include "bsp_bluetooth.h"   /* 本模块头文件 */
#include "control_mode.h"    /* 解析出指令后交给控制模式模块执行 */

extern UART_HandleTypeDef huart1;   /* HC-04蓝牙接在USART1 */

#define BT_SOF1          0xAA   /* 帧头第一个字节 */
#define BT_SOF2          0x55   /* 帧头第二个字节 */
#define BT_RX_BUF_SIZE   64     /* 接收数据缓冲大小 */

/* 蓝牙接收状态机的各个状态 */
typedef enum
{
    BT_STATE_SOF1 = 0,   /* 等待帧头1 */
    BT_STATE_SOF2,       /* 等待帧头2 */
    BT_STATE_LEN,        /* 等待长度 */
    BT_STATE_CMD,        /* 等待指令 */
    BT_STATE_DATA,       /* 等待数据 */
    BT_STATE_CHECK       /* 等待校验 */
} Bluetooth_RxState_t;

static Bluetooth_RxState_t g_state = BT_STATE_SOF1;   /* 当前接收状态 */
static uint8_t g_rx_buf[BT_RX_BUF_SIZE];              /* 接收到的指令+数据 */
static uint8_t g_rx_len = 0;                          /* 已收到的指令+数据字节数 */
static uint8_t g_rx_need = 0;                         /* 还需要收到的字节数（含指令） */
static uint8_t g_rx_total = 0;                        /* LEN字段记录的CMD+DATA总长度 */
static uint8_t g_rx_cmd = 0;                          /* 当前指令码 */

/* 初始化：状态机回到等待帧头 */
void Bluetooth_Init(void)
{
    g_state = BT_STATE_SOF1;   /* 等待帧头1 */
    g_rx_len = 0;              /* 长度清零 */
    g_rx_need = 0;             /* 需求清零 */
    g_rx_total = 0;            /* 总长清零 */
    g_rx_cmd = 0;              /* 指令清零 */
}

/* 校验和：LEN+CMD+DATA所有字节相加，取低8位 */
static uint8_t Bluetooth_CheckSum(uint8_t len, uint8_t cmd, const uint8_t *data, uint8_t data_len)
{
    uint8_t sum = len;          /* 先加上LEN */
    uint8_t i;                  /* 循环变量 */
    sum += cmd;                 /* 加上指令 */
    for (i = 0; i < data_len; i++) {   /* 遍历数据 */
        sum += data[i];                /* 累加每个数据字节 */
    }
    return sum;                 /* 返回低8位 */
}

/* 发送一帧：自动添加帧头、长度和校验 */
void Bluetooth_SendFrame(uint8_t cmd, const uint8_t *data, uint8_t len)
{
    uint8_t buf[BT_RX_BUF_SIZE + 4];   /* 完整帧缓冲 */
    uint8_t total = len + 1;           /* CMD+DATA总长度 */
    uint8_t check;                     /* 校验和 */

    buf[0] = BT_SOF1;                  /* 帧头1 */
    buf[1] = BT_SOF2;                  /* 帧头2 */
    buf[2] = total;                    /* 长度字段 */
    buf[3] = cmd;                      /* 指令字段 */
    if (len > 0) {                     /* 如果有数据 */
        memcpy(&buf[4], data, len);    /* 复制数据到缓冲 */
    }
    check = Bluetooth_CheckSum(total, cmd, data, len);   /* 计算校验和 */
    buf[4 + len] = check;              /* 放入校验字段 */

    HAL_UART_Transmit(&huart1, buf, (uint16_t)(5 + len), 100);   /* 发送整帧，超时100ms */
}

/* 收到一个字节：按状态机逐字节解析完整帧 */
void Bluetooth_OnRxByte(uint8_t byte)
{
    switch (g_state)   /* 根据当前状态处理 */
    {
    case BT_STATE_SOF1:                    /* 等待帧头1 */
        if (byte == BT_SOF1) { g_state = BT_STATE_SOF2; }   /* 匹配则进入下一状态 */
        break;

    case BT_STATE_SOF2:                    /* 等待帧头2 */
        if (byte == BT_SOF2) { g_state = BT_STATE_LEN; }    /* 匹配则进入长度状态 */
        else if (byte == BT_SOF1) { g_state = BT_STATE_SOF2; } /* 再来一个帧头1则保持 */
        else { g_state = BT_STATE_SOF1; }                   /* 否则回到初始状态 */
        break;

    case BT_STATE_LEN:                     /* 等待长度字段 */
        if (byte >= 1 && byte <= BT_RX_BUF_SIZE) {          /* 长度合法 */
            g_rx_total = byte;             /* 保存总长 */
            g_rx_need = byte;              /* 还需要读取byte个字节（含指令） */
            g_rx_len = 0;                  /* 已读清空 */
            g_state = BT_STATE_CMD;        /* 进入读取指令状态 */
        } else {
            g_state = BT_STATE_SOF1;       /* 长度非法，回到初始状态 */
        }
        break;

    case BT_STATE_CMD:                     /* 读取指令码 */
        g_rx_cmd = byte;                   /* 保存指令 */
        g_rx_need--;                       /* 剩余字节减1 */
        if (g_rx_need == 0) { g_state = BT_STATE_CHECK; }   /* 没有数据则直接等待校验 */
        else { g_state = BT_STATE_DATA; }                   /* 有数据则进入数据状态 */
        break;

    case BT_STATE_DATA:                    /* 读取数据 */
        g_rx_buf[g_rx_len++] = byte;       /* 保存一个数据字节 */
        g_rx_need--;                       /* 剩余字节减1 */
        if (g_rx_need == 0) { g_state = BT_STATE_CHECK; }   /* 数据读完等待校验 */
        break;

    case BT_STATE_CHECK:                   /* 校验和检查 */
        {
            uint8_t check = Bluetooth_CheckSum(g_rx_total, g_rx_cmd, g_rx_buf, g_rx_len);   /* 计算校验和 */
            if (check == byte) {           /* 校验通过 */
                ControlMode_OnCommand(g_rx_cmd, g_rx_buf, g_rx_len);   /* 交给控制模式执行 */
            }
        }
        g_state = BT_STATE_SOF1;           /* 无论通过与否，都回到等待下一帧 */
        break;

    default:
        g_state = BT_STATE_SOF1;           /* 未知状态，回到初始状态 */
        break;
    }
}
