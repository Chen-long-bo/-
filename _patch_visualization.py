from pathlib import Path

# 网站首页同步 2026-10-21 控制方案
p=Path('visualization/index.html')
t=p.read_text(encoding='utf-8-sig')
t=t.replace('从电脑摇杆到四个轮子，从编码器计数到 PID 曲线。这里不是一张说明书，而是一张可以点、可以调、可以验证的工程地图。','从电脑按键到四个轮子，从编码器计数到位置曲线。这里不是一张说明书，而是一张可以点、可以调、可以验证的工程地图。')
t=t.replace('模式状态机、加速度平滑、位置 PID、定时旋转与路线。','模式状态机、位置 PID（仅控制与测试页）、定时旋转与路线。')
t=t.replace('<div role="listitem"><b>01</b><span>摇杆采样</span><code>_manual_tick()</code></div>','<div role="listitem"><b>01</b><span>按键/WASD 采样</span><code>_manual_tick()</code></div>')
t=t.replace('                <option value="brake-soft">0x03 缓停</option>\n','')
t=t.replace('                <option value="accel">0x0E 设置加速度</option>\n','')
p.write_text(t, encoding='utf-8')

# 网站数据同步
p=Path('visualization/app.js')
t=p.read_text(encoding='utf-8-sig')
t=t.replace("role: '管理空闲、手动、缓停、位置停、路线和旋转模式。'","role: '管理空闲、手动、位置控制、路线和旋转模式。'")
t=t.replace("tech: '状态机 + 平滑 + PID + 遥测'","tech: '状态机 + PID（仅测试页） + 遥测'")
t=t.replace("role: '不碰硬件的纯算法：麦轮、CPR、旋转时间、加速度。'","role: '不碰硬件的纯算法：麦轮、CPR、旋转时间。'")
# 删除已废弃参数
for name in ['CFG_ACCEL_V','CFG_ACCEL_W','CFG_SOFT_BRAKE_DECEL']:
    import re
    t=re.sub(rf"\s*\{{\s*name: '{name}'.*?\}},", '', t)
# 删除已废弃协议命令
t=t.replace("    'brake-soft': { cmd: 0x03, name: '缓停' },\n","")
t=t.replace("    accel: { cmd: 0x0e, name: '设置加速度' }\n","")
t=t.replace("    'brake-soft': `<label>减速档位 / 0~255<input id=\"proto-decel\" type=\"number\" min=\"0\" max=\"255\" step=\"1\" value=\"0\" inputmode=\"numeric\"></label>`,\n","")
t=t.replace("    accel: `<label>线加速度 / m/s²<input id=\"proto-av\" type=\"number\" step=\"0.01\" value=\"1.0\" inputmode=\"decimal\"></label><label>角加速度 / rad/s²<input id=\"proto-aw\" type=\"number\" step=\"0.01\" value=\"3.0\" inputmode=\"decimal\"></label>`,\n","")
t=t.replace("    if (command === 'brake-soft') return [Math.round(num('proto-decel')) & 0xff];\n","")
t=t.replace("    if (command === 'accel') return [...uint16LE(num('proto-av') * 1000), ...uint16LE(num('proto-aw') * 1000)];\n","")
# 删除加速度解码分支
t=re.sub(r"\s*\} else if \(cmd === 0x0e && data\.length >= 4\) \{.*?\n    \}", "", t, flags=re.S)
p.write_text(t, encoding='utf-8')
print('visualization updated')
