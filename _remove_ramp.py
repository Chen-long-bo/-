from pathlib import Path
import re

# 删除测试工程中的加速度平滑算法和 ramp 命令
h = Path('Test_Project/MecanumTest/Test/debug_algo.h')
t = h.read_text(encoding='utf-8-sig')
t = re.sub(r'float DebugAlgo_RampStep\([^\n]+\);\s*/\* 加速度平滑一步 \*/\s*\n?', '', t)
h.write_text(t, encoding='utf-8')

c = Path('Test_Project/MecanumTest/Test/debug_algo.c')
t = c.read_text(encoding='utf-8-sig')
t = re.sub(r'\n/\* 加速度平滑一步.*\Z', '\n', t, flags=re.S)
c.write_text(t, encoding='utf-8')

app = Path('Test_Project/MecanumTest/Test/test_app.c')
t = app.read_text(encoding='utf-8-sig')
t = t.replace('    Test_Print("ramp <v0> <v1> <accel>       - print accel ramp timeline\\r\\n");\n', '')
t = re.sub(r'static void Test_Ramp\(const char \*arg\)\s*\{.*?\n\}\n\n(?=static void Test_PidStep)', '', t, flags=re.S)
t = t.replace('    else if (strncmp(line, "ramp ", 5) == 0) { Test_Ramp(line + 5); }\n', '')
app.write_text(t, encoding='utf-8')
print('test project ramp removal complete')
