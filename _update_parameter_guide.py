from pathlib import Path
import json

path = Path('PC_上位机/parameter_guide.json')
data = json.loads(path.read_text(encoding='utf-8-sig'))
rows = data['parameters']
existing = {row['name'] for row in rows}

def add(row):
    if row['name'] not in existing:
        rows.append(row)
        existing.add(row['name'])

add({"category":"上位机","name":"WHEEL_DIAMETER_MM","value":"80.0","unit":"mm","kind":"运行期","source":"PC_上位机/config.py","meaning":"上位机计算位置/距离时使用的轮径，必须与固件一致。","increase":"同样编码器计数会被解释为更大距离。","decrease":"同样编码器计数会被解释为更小距离。","test":"卡尺测量并走 1000mm 对照。","range":"按实车，约60~100mm","warning":"与 STM32 config.h 不一致会导致 PC 位置曲线和固件控制不同步。"})
add({"category":"上位机","name":"WHEELBASE_MM","value":"130.0","unit":"mm","kind":"运行期","source":"PC_上位机/config.py","meaning":"上位机几何预览使用的前后轮中心距。","increase":"旋转/横移预览轮速差增大。","decrease":"旋转/横移预览轮速差减小。","test":"量前轮中心到后轮中心。","range":"按实车","warning":"必须和 STM32 的 CFG_WHEELBASE_MM 保持一致。"})
add({"category":"上位机","name":"TRACK_MM","value":"123.5","unit":"mm","kind":"运行期","source":"PC_上位机/config.py","meaning":"上位机几何预览使用的左右轮中心距。","increase":"旋转/横移预览轮速差增大。","decrease":"旋转/横移预览轮速差减小。","test":"量左侧轮中心到右侧轮中心。","range":"按实车","warning":"必须和 STM32 的 CFG_TRACK_MM 保持一致。"})
add({"category":"上位机","name":"MIN_DRIVE","value":"0.30","unit":"归一化","kind":"固件参考","source":"PC_上位机/config.py / STM32 config.h","meaning":"低速最小驱动参考值；真正生效的是固件 CFG_MIN_DRIVE。","increase":"上位机标定参考值变大，实车低速更不容易抖但起步更猛。","decrease":"低速更细但更容易震动。","test":"用测试工程 min 命令从0.10逐步增加。","range":"0.05~0.50","warning":"PC 改动不会自动改固件，必须同步烧录。"})
add({"category":"上位机","name":"BAUDRATE_OPTIONS","value":"9600/115200","unit":"bps","kind":"运行期","source":"PC_上位机/config.py","meaning":"串口波特率下拉选项；COM7蓝牙用9600，COM5调试用115200。","increase":"提高调试链路速率。","decrease":"降低速率，兼容性更好。","test":"选对应端口后观察是否有 AA55 数据。","range":"9600/115200","warning":"必须与设备和固件配置一致。"})
add({"category":"界面","name":"WINDOW_W","value":"1280","unit":"px","kind":"运行期","source":"PC_上位机/config.py","meaning":"主窗口默认宽度。","increase":"显示更多列和曲线。","decrease":"窗口更紧凑。","test":"启动后观察布局。","range":"1000~1920","warning":"过小会挤压按钮，不影响控制。"})
add({"category":"界面","name":"WINDOW_H","value":"820","unit":"px","kind":"运行期","source":"PC_上位机/config.py","meaning":"主窗口默认高度。","increase":"显示更多曲线和参数行。","decrease":"窗口更紧凑。","test":"启动后观察布局。","range":"700~1200","warning":"过小会需要滚动，不影响控制。"})

for item in data.get('assumptions', []):
    if item.get('item') == '麦轮辊轮方向':
        item['current'] = '按车轮布局.jpg 俯视图：A 辊轮轴向右上（/），B 向右下（\\），C 向右下（\\），D 向右上（/）；电机/编码器符号仍需单轮测试。'
        item['confirm'] = '对照车轮布局.jpg、单轮转动和整车前后/横移/旋转测试'
        item['impact'] = '辊轮方向与运动学公式不匹配会导致横移或旋转方向错误。'

path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print('parameters', len(rows), 'assumptions', len(data.get('assumptions', [])))
