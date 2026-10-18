import serial, time
import protocol
s=serial.Serial("COM5",115200,timeout=0.2)
s.reset_input_buffer()
time.sleep(0.3)
s.reset_input_buffer()
hb=protocol.cmd_heartbeat()
s.write(hb)
time.sleep(0.5)
d=s.read(8192)
s.close()
ack=bytes([0xAA,0x55,0x03,0x83,0x0A,0x00,0x90])
print("len",len(d),"ACK found:", ack in d)
print("first 120:", d[:120].hex(" ").upper())
