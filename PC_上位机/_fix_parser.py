# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\protocol.py"
lines = open(p, encoding="utf-8").read().split("\n")
out = []
for ln in lines:
    out.append(ln)
    if "self.need = 0" in ln and "还需要读取" in ln:
        out.append("        self.length = 0                          # 当前帧的LEN字段")
    if "self.need = byte" in ln and "还需要读CMD+DATA" in ln:
        out.append("                self.length = byte               # 保存LEN，校验时要用")
open(p, "w", encoding="utf-8").write("\n".join(out))
print("inserted")
