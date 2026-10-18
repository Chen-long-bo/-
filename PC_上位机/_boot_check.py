import serial, subprocess, time
try:
    s=serial.Serial("COM5",115200,timeout=0.5)
except Exception as e:
    print("OPEN FAIL", repr(e)); raise SystemExit
s.reset_input_buffer()
subprocess.run(["python","-m","pyocd","cmd","-t","cortex_m","-c","reset"],timeout=60,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(0.8)
d=s.read(2048)
print("BOOT RX:", d)
s.close()
