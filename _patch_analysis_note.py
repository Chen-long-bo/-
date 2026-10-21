from pathlib import Path
p=Path('工程只读分析报告.md')
t=p.read_text(encoding='utf-8-sig')
note='> **2026-10-21 变更提示**：普通控制中的缓起/缓停/加速度平滑已删除，PID 仅在控制与测试页使用；本报告是历史只读分析，当前参数以 `PC_上位机/parameter_guide.json` 和 `本次修改说明_2026-10-21.md` 为准。\n\n'
if '2026-10-21 变更提示' not in t:
    t=note+t
p.write_text(t,encoding='utf-8')
print('analysis report note added')
