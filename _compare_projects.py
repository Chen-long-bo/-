from pathlib import Path
import re
for name in ['STM32_Project/CubeMX/MecanumCar/MDK-ARM/MecanumCar.uvprojx','Test_Project/MecanumTest/MDK-ARM/MecanumTest.uvprojx']:
    t=Path(name).read_text(encoding='utf-8-sig')
    print('\n===',name,'===')
    for key in ['pCCUsed','uAC6','TargetName','OutputName','CreateHexFile','Device','Vendor','Cpu','FlashDriverDll']:
        vals=re.findall(fr'<{key}>(.*?)</{key}>',t,re.S)
        print(key, vals[:5])
