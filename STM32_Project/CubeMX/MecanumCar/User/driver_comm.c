#include "main.h"          /* HAL库和UART句柄 */
#include <stdio.h>         /* sscanf解析 */
#include <string.h>        /* memset */
#include "driver_comm.h"   /* 本模块头文件 */

extern UART_HandleTypeDef huart2;   /* 驱动模块接USART2 */

static char g_line[128];            /* 一条完整响应（以!结尾） */
static uint8_t g_line_len = 0;      /* 当前响应已收字节数 */
static DriverComm_Data_t g_data;    /* 最新数据 */

/* 初始化 */
void DriverComm_Init(void)
{
    memset(&g_data, 0, sizeof(g_data));   /* 数据清零 */
    memset(g_line, 0, sizeof(g_line));    /* 缓冲清零 */
    g_line_len = 0;                       /* 长度清零 */
}

/* 发送一段文本 */
static void DriverComm_SendString(const char *str)
{
    HAL_UART_Transmit(&huart2, (uint8_t *)str, (uint16_t)strlen(str), 100);   /* 阻塞发送 */
}

/* 把浮点数格式化为固定3位小数字符串，避免依赖%f */
static void DriverComm_FormatFloat(char *out, float v)
{
    int permille = (int)(v * 1000.0f);          /* 放大1000倍 */
    int neg = (permille < 0) ? 1 : 0;           /* 是否为负 */
    int abs = neg ? (-permille) : permille;     /* 取绝对值 */
    int ip = abs / 1000;                        /* 整数部分 */
    int fp = abs % 1000;                        /* 小数部分 */

    if (neg) { *out++ = '-'; }                  /* 负号 */
    sprintf(out, "%d.%03d", ip, fp);            /* 整数格式化 */
}

/* 发送四轮闭环转速指令：$Car:四轮速度!，每轮范围-1~1 */
void DriverComm_SendCar(float w1, float w2, float w3, float w4)
{
    char f0[10], f1[10], f2[10], f3[10];   /* 四轮浮点字符串 */
    char buf[64];                          /* 指令缓冲 */

    DriverComm_FormatFloat(f0, w1);        /* 格式化 */
    DriverComm_FormatFloat(f1, w2);
    DriverComm_FormatFloat(f2, w3);
    DriverComm_FormatFloat(f3, w4);
    sprintf(buf, "$Car:%s,%s,%s,%s!", f0, f1, f2, f3);   /* 拼接 */
    DriverComm_SendString(buf);            /* 发送 */
}

/* 设置电机类型为520：0=520 */
void DriverComm_SetMotorType520(void)
{
    DriverComm_SendString("$MOTOR_4CH_SET:0!");
}

/* 设置轮径/编码器线数/减速比 */
void DriverComm_SetMotorParam(uint8_t dia_cm, uint8_t lines, uint8_t ratio)
{
    char buf[64];
    sprintf(buf, "$MOTOR_PARAM:%d,%d,%d!", dia_cm, lines, ratio);
    DriverComm_SendString(buf);
}

/* 请求20ms计数 */
void DriverComm_RequestEncoder20ms(void)
{
    DriverComm_SendString("$MOTOR_4CH_READ:encoder_20ms!");
}

/* 请求累计计数 */
void DriverComm_RequestEncoderTotal(void)
{
    DriverComm_SendString("$MOTOR_4CH_READ:encoder_total!");
}

/* 请求电池电压 */
void DriverComm_RequestBattery(void)
{
    DriverComm_SendString("$MOTOR_4CH_READ:battery!");
}

/* 收到一个字节：拼字符串，遇!解析 */
void DriverComm_OnRxByte(uint8_t byte)
{
    if (g_line_len >= sizeof(g_line) - 1) { g_line_len = 0; }   /* 防溢出 */

    if (byte == '!') {                                           /* 一条响应完整 */
        g_line[g_line_len] = '\0';                               /* 结束符 */

        if (sscanf(g_line, "$MOTOR_4CH_Encoder_20ms:%hd,%hd,%hd,%hd",
                   (short *)&g_data.encoder_20ms[0], (short *)&g_data.encoder_20ms[1],
                   (short *)&g_data.encoder_20ms[2], (short *)&g_data.encoder_20ms[3]) == 4) {
            g_data.encoder_20ms_ok = 1;                          /* 20ms已更新 */
        }
        else if (sscanf(g_line, "$MOTOR_4CH_Encoder_Total:%d,%d,%d,%d",
                        &g_data.encoder_total[0], &g_data.encoder_total[1],
                        &g_data.encoder_total[2], &g_data.encoder_total[3]) == 4) {
            g_data.encoder_total_ok = 1;                         /* 累计已更新 */
        }
        else if (sscanf(g_line, "$MOTOR_4CH_Battery:%hu", &g_data.battery_raw) == 1) {
            /* 电压解析成功 */
        }
        g_line_len = 0;                                          /* 清空准备下一条 */
    }
    else {
        g_line[g_line_len++] = (char)byte;                       /* 普通字符存入 */
    }
}

/* 获取数据指针 */
DriverComm_Data_t *DriverComm_GetData(void)
{
    return &g_data;
}
