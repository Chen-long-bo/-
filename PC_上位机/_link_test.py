import serial, time
import protocol
try:
    s = serial.Serial("COM5", 115200, timeout=0.5)
except Exception as e:
    print("COM5 OPEN FAIL:", repr(e))
    raise SystemExit
s.reset_input_buffer()
hb = protocol.cmd_heartbeat()
print("TX:", hb.hex(" ").upper())
s.write(hb)
time.sleep(1.0)
data = s.read(4096)
print("RX(", len(data), "bytes):", data.hex(" ").upper())
s.close()
