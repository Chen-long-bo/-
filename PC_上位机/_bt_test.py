import serial, time
import protocol
for port in ("COM8","COM7"):
    print("== try", port)
    try:
        s=serial.Serial(port,9600,timeout=0.5)
    except Exception as e:
        print("  OPEN FAIL", repr(e)); continue
    s.reset_input_buffer()
    s.write(protocol.cmd_heartbeat())
    time.sleep(1.0)
    d=s.read(4096)
    print("  RX", len(d), "bytes; heartbeat ACK:", bytes([0xAA,0x55,0x03,0x83,0x0A,0x00,0x90]) in d)
    s.close()
