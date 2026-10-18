import serial, time
import protocol
port="COM7"
print("open", port)
try:
    s=serial.Serial(port,9600,timeout=0.5,write_timeout=2.0)
except Exception as e:
    print("OPEN FAIL", repr(e)); raise SystemExit
print("OPEN OK")
s.reset_input_buffer()
try:
    s.write(protocol.cmd_heartbeat())
    print("heartbeat sent")
except Exception as e:
    print("WRITE FAIL", repr(e))
time.sleep(1.2)
d=s.read(4096)
print("RX bytes:", len(d))
ack=bytes([0xAA,0x55,0x03,0x83,0x0A,0x00,0x90])
print("ACK found:", ack in d)
if d:
    print("first 80:", d[:80].hex(" ").upper())
s.close()
