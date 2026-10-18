#ifndef __USER_APP_H
#define __USER_APP_H

/* 用户程序总入口：把这两个函数放进CubeMX生成的main.c里调用即可 */
void User_Init(void);    /* 初始化所有模块，放在外设初始化之后 */
void User_Loop(void);    /* 主循环调用，放在main.c的while(1)里 */

#endif /* __USER_APP_H */
