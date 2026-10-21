import xml.etree.ElementTree as ET
from pathlib import Path
p=Path(r'STM32_Project/CubeMX/MecanumCar/MDK-ARM/MecanumCar.uvprojx')
root=ET.parse(p).getroot()
base=p.parent
missing=[]
for e in root.iter('FilePath'):
    fp=e.text
    if not fp: continue
    q=(base/fp).resolve()
    if not q.exists(): missing.append((fp,str(q)))
print('target:', [e.text for e in root.iter('TargetName')])
print('missing',len(missing))
for x in missing[:20]: print(x)
print('groups',len(list(root.iter('Group'))),'files',len(list(root.iter('File'))))
