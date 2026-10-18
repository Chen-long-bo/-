import asyncio
from bleak import BleakScanner
async def main():
    print("scanning 8s with adv data...")
    result = await BleakScanner.discover(timeout=8.0, return_adv=True)
    for addr, (dev, adv) in result.items():
        name = adv.local_name
        uuids = adv.service_uuids
        if name or (uuids and any("ffe0" in u.lower() for u in uuids)):
            print(addr, "| name:", name, "| rssi:", adv.rssi, "| uuids:", uuids)
asyncio.run(main())
