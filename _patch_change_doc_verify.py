from pathlib import Path
p=Path('本次修改说明_2026-10-21.md')
t=p.read_text(encoding='utf-8-sig')
t=t.replace('- 主工程 ST-Link 烧录：Erase Done / Programming Done / Verify OK。','- 主工程 ST-Link 烧录：Erase Done / Programming Done / Verify OK；\n- 烧录后使用 `python -m pyocd commander -t cortex_m -c reset go` 让 MCU 退出停止状态并运行；\n- COM7 实机链路测试：收到 0x81 状态帧和 0x82 曲线帧，电池约 12655 mV。')
p.write_text(t,encoding='utf-8')
print('verification note updated')
