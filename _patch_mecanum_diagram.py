from pathlib import Path
p = Path('diagrams/_generate_diagrams.py')
t = p.read_text(encoding='utf-8-sig')
start = t.index('# 3 mecanum layout')
end = t.index('# 4 encoder AB')
new = '''# 3 mecanum layout（按实车轮布局.jpg：A /，B \\，C \\，D /）
b=t(30,32,"麦克纳姆轮布局与运动学（按实车辊轮方向）",20,"#ffffff","start","bold")
b+=f'<rect x="330" y="110" width="420" height="260" rx="16" fill="{PANEL}" stroke="{BORDER}" stroke-width="2"/>'
b+=t(540,140,"车体俯视图",15,"#ffffff","middle","bold")
# 外圈矩形是轮子外轮廓；内部斜矩形是辊轮方向和大致轮廓
wheel_specs = [(300,130,"A","-45"),(760,130,"B","45"),(300,300,"C","45"),(760,300,"D","-45")]
for (x,y,label,angle) in wheel_specs:
    b+=f'<rect x="{x}" y="{y}" width="50" height="90" rx="8" fill="{PANEL2}" stroke="{YEL}" stroke-width="2"/>'
    cx=x+25
    cy=y+45
    b+=f'<rect x="{cx-7}" y="{cy-27}" width="14" height="54" rx="3" fill="#0E0F13" stroke="{ACC}" stroke-width="1.5" transform="rotate({angle} {cx} {cy})"/>'
    b+=t(cx,y+45,label,16,YEL,"middle","bold")
b+=t(300,245,"A 左前：/",12,SUB)
b+=t(760,245,"B 右前：\\\\",12,SUB)
b+=t(300,415,"C 左后：\\\\",12,SUB)
b+=t(760,415,"D 右后：/",12,SUB)
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
b+=t(600,550,"A /，B \\\\，C \\\\，D /（俯视图）；电机/编码器符号仍需实测",13,YEL)
b+=t(600,575,"若某个轮方向反，优先调整该轮符号或接线，不要盲目改整个公式",12,SUB)
save("mecanum_layout.svg",1000,620,b)

'''
p.write_text(t[:start] + new + t[end:], encoding='utf-8')
print('generator patched')
