# -*- coding: utf-8 -*-
import os, html
out = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\diagrams"
os.makedirs(out, exist_ok=True)

BG="#0E0F13"; PANEL="#15161C"; PANEL2="#1B1D25"; BORDER="#2A2D38"; TEXT="#E6E8EF"; SUB="#8A8F9E"; ACC="#00D1B2"; BLUE="#4F8CFF"; RED="#FF5C6C"; YEL="#FFC857"

def t(x,y,s,size=13,color=TEXT,anchor="start",weight="normal"):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{html.escape(str(s))}</text>'

def box(x,y,w,h,title,lines=None,stroke=ACC,fill=PANEL):
    s=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    s+=t(x+w/2,y+24,title,15,"#ffffff","middle","bold")
    if lines:
        for i,line in enumerate(lines):
            s+=t(x+14,y+48+i*20,line,12,SUB)
    return s

def arrow(x1,y1,x2,y2,color=ACC,label=None,lx=None,ly=None):
    s=f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2" marker-end="url(#arrow{color[1:]})"/>'
    if label:
        s+=t(lx if lx is not None else (x1+x2)/2, ly if ly is not None else (y1+y2)/2-6,label,11,color)
    return s

def defs():
    s='<defs>'
    for c in [ACC,BLUE,RED,YEL,SUB]:
        s+=f'<marker id="arrow{c[1:]}" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="{c}"/></marker>'
    s+='</defs>'
    return s

def save(name,w,h,body):
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="Microsoft YaHei, SimHei, Arial, sans-serif">{defs()}<rect width="{w}" height="{h}" fill="{BG}"/>{body}</svg>'
    open(os.path.join(out,name),"w",encoding="utf-8").write(svg)
    print("wrote",name)

# 1 system architecture
b=t(30,32,"麦轮小车 — 系统架构（硬件+软件分层）",20,"#ffffff","start","bold")
b+=box(30,70,230,110,"PC 上位机",["PySide6 UI / 协议 / 串口"],BLUE)
b+=box(320,70,190,110,"HC-04 蓝牙",["SPP 9600 / 透传"],BLUE)
b+=box(570,60,300,190,"STM32F407VET6",["USART1：蓝牙 9600","USART2：驱动模块 115200","USART3：调试/COM5 115200","控制：麦轮/PID/平滑/遥测"],ACC)
b+=box(570,350,300,150,"四路编码器电机驱动模块",["$Car 闭环速度","读编码器/电压","AT8236 H 桥 ×4"],RED)
b+=box(930,350,140,150,"四个电机",["A/B/C/D","麦克纳姆轮"],YEL)
b+=box(930,160,140,140,"四个编码器",["A/B 相","11PPR×56×4"],BLUE)
b+=box(30,330,230,100,"3S 锂电池",["12.4V 标称 / 12.6V 满电"],RED)
b+=box(30,500,280,110,"稳压模块",["12V → 驱动模块","5V → STM32","3.3V → HC-04"],RED)
b+=arrow(260,125,320,125,BLUE,"蓝牙")
b+=arrow(510,125,570,125,BLUE,"UART1")
b+=arrow(720,250,720,350,RED,"UART2")
b+=arrow(870,425,930,425,RED,"电机线")
b+=arrow(1000,350,1000,300,BLUE,"编码器")
b+=box(930,70,140,60,"USB-TTL",["COM5 调试"],SUB)
b+=arrow(930,100,870,100,SUB,"USART3")
b+=arrow(145,330,145,500,RED,"电池")
b+=arrow(310,555,570,555,RED,"12V/5V/3.3V")
b+=t(30,680,"注意：所有 GND 共地；驱动模块 UART 的 5V 不要接 STM32；电机/编码器先核对 6P 线序。",12,YEL)
save("system_architecture.svg",1100,720,b)

# 2 data flow
b=t(30,32,"麦轮小车 — 完整数据流（指令 + 反馈）",20,"#ffffff","start","bold")
b+=box(30,70,250,110,"PC 上位机",["MainWindow._manual_tick()","protocol.cmd_manual()","SerialWorker.send_frame()"],BLUE)
b+=box(330,70,210,110,"HC-04 / COM5",["蓝牙SPP 或 有线"],BLUE)
b+=box(590,60,280,150,"STM32 协议/应用",["USARTx_IRQHandler()","HAL_UART_RxCpltCallback()","Bluetooth_OnRxByte()","ControlMode_OnCommand()"],ACC)
b+=box(590,270,280,150,"STM32 控制/运动学",["ControlMode_Poll()","RampToward()","ControlMode_RunSpeedLoop()","Chassis_Inverse()"],ACC)
b+=box(590,480,280,130,"STM32 执行/通信",["Motor_SetSpeed()","DriverComm_SendCar()","HAL_UART_Transmit(huart2)"],ACC)
b+=box(930,480,140,130,"驱动模块",["$Car 闭环","AT8236"],RED)
b+=box(930,270,140,130,"四个电机",["A/B/C/D"],YEL)
b+=box(930,70,140,130,"四个编码器",["A/B 相"],BLUE)
b+=arrow(280,125,330,125,BLUE,"")
b+=arrow(540,125,590,125,BLUE,"")
b+=arrow(730,210,730,270,ACC,"")
b+=arrow(730,420,730,480,ACC,"")
b+=arrow(870,545,930,545,RED,"")
b+=arrow(1000,480,1000,400,BLUE,"反馈")
b+=box(30,270,250,120,"反馈到 PC",["DriverComm_OnRxByte()","bsp_encoder 换算","SendStatus/SendCurve()","Bluetooth_SendFrame()"],BLUE)
b+=arrow(590,480,280,480,BLUE,"")
b+=arrow(280,390,280,480,BLUE,"")
b+=arrow(590,120,280,120,BLUE,"")
b+=box(330,480,210,130,"PC 反馈解析",["SerialWorker.run()","FrameParser.feed()","_on_status/_on_curve()"],BLUE)
b+=t(30,700,"蓝线：指令/反馈数据；绿线：STM32 内部；红线：驱动/电机。所有函数名可在代码地图中定位。",12,YEL)
save("data_flow.svg",1120,730,b)

# 3 mecanum layout
b=t(30,32,"麦克纳姆轮布局与运动学（X 型）",20,"#ffffff","start","bold")
b+=f'<rect x="330" y="110" width="420" height="260" rx="16" fill="{PANEL}" stroke="{BORDER}" stroke-width="2"/>'
b+=t(540,140,"车体俯视图",15,"#ffffff","middle","bold")
# wheels
for (x,y,label) in [(300,130,"A 左前"),(760,130,"B 右前"),(300,300,"C 左后"),(760,300,"D 右后")]:
    b+=f'<rect x="{x}" y="{y}" width="50" height="90" rx="8" fill="{PANEL2}" stroke="{YEL}" stroke-width="2"/>'
    b+=t(x+25,y+45,label.split()[0],16,YEL,"middle","bold")
b+=t(300,245,"A 左前",12,SUB)
b+=t(760,245,"B 右前",12,SUB)
b+=t(300,415,"C 左后",12,SUB)
b+=t(760,415,"D 右后",12,SUB)
b+=arrow(540,240,640,240,BLUE,"vx 前进")
b+=arrow(540,240,540,160,BLUE,"vy 左")
b+=f'<path d="M 520 260 A 45 45 0 0 1 560 260" fill="none" stroke="{YEL}" stroke-width="2"/>'
b+=t(565,275,"wz 逆时针+",11,YEL)
b+=t(30,470,"逆运动学（轮子线速度，m/s）：",15,"#ffffff","start","bold")
b+=t(30,500,"A = vx - vy - (a+b)·wz",14,ACC)
b+=t(30,525,"B = vx + vy + (a+b)·wz",14,ACC)
b+=t(30,550,"C = vx + vy - (a+b)·wz",14,ACC)
b+=t(30,575,"D = vx - vy + (a+b)·wz",14,ACC)
b+=t(600,500,"a = 轴距/2，b = 轮距/2",13,SUB)
b+=t(600,525,"当前：轴距 130mm，轮距 123.5mm",13,SUB)
b+=t(600,550,"注意：若实车方向反，先确认辊轮是 X 型还是 O 型",13,YEL)
save("mecanum_layout.svg",1000,620,b)

# 4 encoder AB
b=t(30,32,"霍尔编码器 A/B 相与 4 倍频",20,"#ffffff","start","bold")
b+=t(30,80,"A 相",13,TEXT)
b+=t(30,140,"B 相",13,TEXT)
# simple square waves
def wave(y,phase):
    pts=[]
    for i in range(0,40):
        x=100+i*20
        yy=y-(18 if ((i+phase)%2==0) else 0)
        pts.append(f"{x},{yy}")
    return " ".join(pts)
b+=f'<polyline points="{wave(80,0)}" fill="none" stroke="{ACC}" stroke-width="2"/>'
b+=f'<polyline points="{wave(140,1)}" fill="none" stroke="{BLUE}" stroke-width="2"/>'
b+=t(30,220,"A、B 相差 90°；正交解码可得到方向 + 计数。",13,SUB)
b+=t(30,250,"每转计数 CPR = 编码器线数 × 减速比 × 倍频数",14,ACC)
b+=t(30,278,"当前假设：11PPR × 56 × 4 = 2464 counts/输出转",14,ACC)
b+=t(30,320,"如果实际 CPR 不同：用测试工程 enczero → 走已知距离 → cpcal <mm> 反算。",13,YEL)
save("encoder_ab.svg",800,380,b)

# 5 PID block
b=t(30,32,"位置环 + 速度环（串级）",20,"#ffffff","start","bold")
b+=box(30,90,150,90,"目标位置",["来自 0x04"],BLUE)
b+=box(230,90,150,90,"误差",["目标 - 实际"],SUB)
b+=box(430,90,180,90,"STM32 位置 PID",["Kp/Ki/Kd","输出目标速度"],ACC)
b+=box(660,90,200,90,"驱动模块速度环",["$Car 内部闭环"],RED)
b+=box(900,90,150,90,"电机/轮子",["实际转动"],YEL)
b+=box(660,270,200,90,"编码器",["20ms/累计计数"],BLUE)
b+=box(430,270,180,90,"bsp_encoder",["计数→速度/距离"],ACC)
b+=arrow(180,135,230,135,BLUE,"")
b+=arrow(380,135,430,135,BLUE,"")
b+=arrow(610,135,660,135,ACC,"")
b+=arrow(860,135,900,135,RED,"")
b+=arrow(975,180,975,315,BLUE,"反馈")
b+=arrow(860,315,660,315,BLUE,"")
b+=arrow(660,315,610,315,ACC,"")
b+=arrow(430,315,380,315,ACC,"")
b+=arrow(380,270,380,180,ACC,"")
b+=t(30,430,"说明：速度环在驱动模块内部，STM32 只做位置环 + 加速度平滑；",13,SUB)
b+=t(30,455,"所以“PID调参”页主要调位置环，速度环参数在模块内部不可直接调。",13,YEL)
save("pid_block.svg",1100,500,b)

# 6 protocol frame
b=t(30,32,"通信协议帧格式（AA 55 LEN CMD DATA CHECK）",20,"#ffffff","start","bold")
fields=[("AA",60),("55",60),("LEN",70),("CMD",70),("DATA ...",260),("CHECK",80)]
x=30
for name,w in fields:
    b+=f'<rect x="{x}" y="90" width="{w}" height="60" rx="6" fill="{PANEL2}" stroke="{ACC}" stroke-width="2"/>'
    b+=t(x+w/2,127,name,14,"#ffffff","middle","bold")
    x+=w+8
b+=t(30,190,"LEN = CMD + DATA 的字节数；CHECK = (LEN + CMD + DATA 所有字节之和) & 0xFF",14,ACC)
b+=t(30,225,"例：心跳帧 AA 55 01 0A 0B",14,TEXT)
b+=t(30,250,"LEN=01, CMD=0A, CHECK=01+0A=0B",13,SUB)
b+=t(30,290,"PC 端：protocol.build_frame() / FrameParser",13,BLUE)
b+=t(30,315,"STM32 端：Bluetooth_SendFrame() / Bluetooth_OnRxByte()",13,ACC)
b+=t(30,355,"注意：两端校验和算法必须完全一致；LEN 也要参与校验。",13,YEL)
save("protocol_frame.svg",900,400,b)

# 7 state machine
b=t(30,32,"控制模式状态机",20,"#ffffff","start","bold")
states={"IDLE":(120,80),"MANUAL":(420,80),"BRAKE_SOFT":(720,80),"POS_STOP":(420,260),"ROTATE":(720,260),"ROUTE":(120,260)}
for name,(x,y) in states.items():
    b+=f'<ellipse cx="{x+80}" cy="{y+40}" rx="80" ry="40" fill="{PANEL}" stroke="{ACC}" stroke-width="2"/>'
    b+=t(x+80,y+45,name,15,"#ffffff","middle","bold")
b+=arrow(200,120,420,120,BLUE,"0x01 手动")
b+=arrow(500,120,720,120,YEL,"0x03 缓停")
b+=arrow(500,120,500,260,ACC,"0x04 PID停")
b+=arrow(800,120,800,260,YEL,"0x0D 旋转")
b+=arrow(200,120,200,260,ACC,"0x05 路线")
b+=arrow(720,300,500,300,SUB,"完成/停止")
b+=arrow(500,300,200,300,SUB,"")
b+=t(30,420,"0x02 急刹 / 0x06 急停：任何状态 → IDLE（立即停车）",13,RED)
b+=t(30,450,"0x01 手动：IDLE/其它 → MANUAL",13,SUB)
b+=t(30,480,"0x03 缓停：MANUAL → BRAKE_SOFT → IDLE",13,SUB)
b+=t(30,510,"0x04 PID停：进入位置环；0x0D 旋转：定时旋转后回 IDLE",13,SUB)
save("state_machine.svg",950,550,b)

# 8 mindmap
b=t(30,32,"麦轮小车工程 — 知识思维导图",20,"#ffffff","start","bold")
cx,cy=550,380
b+=f'<ellipse cx="{cx}" cy="{cy}" rx="110" ry="55" fill="{PANEL2}" stroke="{ACC}" stroke-width="3"/>'
b+=t(cx,cy+6,"麦轮小车工程",17,"#ffffff","middle","bold")
branches=[("硬件",(180,160),["电池/稳压","STM32F407","AT8236驱动","电机/编码器","麦克纳姆轮"]),
          ("通信",(920,150),["UART/波特率","HC-04 SPP","AA55协议","校验和","COM7/COM5"]),
          ("运动学",(150,470),["X/O 布局","vx/vy/wz","逆运动学","轮速归一化","轴距/轮距"]),
          ("控制",(930,470),["位置环 PID","速度环(模块)","加速度平滑","最小驱动","状态机"]),
          ("调试",(550,650),["Keil 编译/烧录","Watch 变量","编码器 CPR","旋转时间","PID 阶跃"]),
          ("安全",(550,110),["急停/缓停","限幅","超时","共地","轮子悬空"])]
for name,(x,y),items in branches:
    b+=f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="{BORDER}" stroke-width="2"/>'
    b+=f'<ellipse cx="{x}" cy="{y}" rx="70" ry="32" fill="{PANEL}" stroke="{BLUE}" stroke-width="2"/>'
    b+=t(x,y+5,name,15,"#ffffff","middle","bold")
    for i,it in enumerate(items):
        b+=t(x,y+48+i*18,it,11,SUB,"middle")
save("mindmap.svg",1100,720,b)

