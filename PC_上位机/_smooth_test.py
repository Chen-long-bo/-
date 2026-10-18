import serial, time, subprocess
import protocol
subprocess.run(["python","-m","pyocd","cmd","-t","cortex_m","-c","reset"],timeout=60,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
s=serial.Serial("COM5",115200,timeout=0.2)
parser=protocol.FrameParser()
def read_for(dur):
    out=[]; end=time.time()+dur
    while time.time()<end:
        d=s.read(512)
        for b in d:
            for cmd,data in parser.feed(b):
                if cmd==0x81:
                    st=protocol.parse_status(data)
                    if st: out.append(st)
    return out
time.sleep(0.4)
read_for(0.3)
s.write(protocol.cmd_manual(0.5,0,0))
frames=read_for(1.2)
s.write(protocol.cmd_stop_all())
print("speed samples (m/s):")
for i,st in enumerate(frames):
    if i % 3 == 0:
        print(round(i*0.03,2), [round(v,3) for v in st["speed"]], "mode", st["mode"])
s.close()
