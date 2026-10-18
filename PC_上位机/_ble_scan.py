import asyncio
from bleak import BleakScanner
async def main():
    print("scanning 8s...")
    devices = await BleakScanner.discover(timeout=8.0)
    for d in devices:
        print(d.address, "|", d.name, "|", getattr(d, "details", ""))
asyncio.run(main())
