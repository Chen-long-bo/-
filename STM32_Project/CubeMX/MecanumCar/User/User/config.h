#ifndef __CONFIG_H
#define __CONFIG_H

/* ============================================================
 * 本文件是唯一调参入口：所有可改参数集中在这里。
 * ============================================================ */

/* 版本 */
#define CFG_FW_VER_MAJOR        0        /* 主版本号 */
#define CFG_FW_VER_MINOR        1        /* 次版本号 */

/* 串口波特率 */
#define CFG_BLUETOOTH_BAUD      9600     /* HC-04蓝牙 */
#define CFG_DRIVER_BAUD         115200   /* 四路驱动模块 */
#define CFG_DEBUG_BAUD          115200   /* USB转串口调试 */

/* 车轮与底盘尺寸（量好后改这里，单位毫米） */
#define CFG_WHEEL_DIAMETER_MM   80.0f    /* 轮径 */
#define CFG_WHEELBASE_MM        200.0f   /* 前后轴距（占位值） */
#define CFG_TRACK_MM            200.0f   /* 左右轮距（占位值） */

/* 编码器：4倍频后每转计数 = 11PPR * 56减速比 * 4 */
#define CFG_ENCODER_CPR         2464.0f

/* 运动限幅 */
#define CFG_MAX_SPEED_M_S       1.0f     /* 最大平移速度 m/s */
#define CFG_MAX_OMEGA_RAD_S     1.0f     /* 最大旋转角速度 rad/s */
#define CFG_MAX_WHEEL_SPEED_M_S 1.0f     /* 轮子线速度上限，用于归一化到 $Car 的 -1~1 */

/* 控制周期 */
#define CFG_LOOP_MS             20       /* 主控制周期 ms */
#define CFG_TELEMETRY_MS        100      /* 状态上报周期 ms */

/* 位置环PID参数（速度环由驱动模块 $Car 内部完成） */
#define CFG_POS_KP              0.8f     /* 位置环比例 */
#define CFG_POS_KI              0.0f     /* 位置环积分 */
#define CFG_POS_KD              0.0f     /* 位置环微分 */

/* 缓停参数：每20ms减少的速度 m/s */
#define CFG_SOFT_BRAKE_DECEL    0.02f

/* 固定路线：正方形边长 mm */
#define CFG_ROUTE_SIDE_MM       800

#endif /* __CONFIG_H */
