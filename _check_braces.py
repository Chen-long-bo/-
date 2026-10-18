import os, re
udir = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\STM32_Project\User"
for fn in sorted(os.listdir(udir)):
    if not fn.endswith(".c") and not fn.endswith(".h"):
        continue
    p = os.path.join(udir, fn)
    text = open(p, encoding="utf-8").read()
    # 去掉字符串字面量和行注释，粗略统计括号是否平衡
    text2 = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    text2 = re.sub(r"'(?:\\.|[^'\\])*'", "''", text2)
    text2 = re.sub(r'//[^\n]*', '', text2)
    text2 = re.sub(r'/\*.*?\*/', '', text2, flags=re.S)
    counts = {c: text2.count(c) for c in '{}()[]'}
    ok = counts['{']==counts['}'] and counts['(']==counts[')'] and counts['[']==counts[']']
    print(fn, "OK" if ok else "MISMATCH", counts)
