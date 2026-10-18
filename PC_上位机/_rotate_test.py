import serial, time, math
import protocol
s=serial.Serial("COM5",115200,timeout=0.2)
parser=protocol.FrameParser()
def read_frames(dur):
    frames=[]; end=time.time()+dur
    while time.time()<end:
        d=s.read(512)
        for b in d:
            for cmd,data in parser.feed(b):
                frames.append((cmd,data))
    return frames
def last_status(frames):
    st=None
    for cmd,data in frames:
        if cmd==0x81:
            x=protocol.parse_status(data)
            if x: st=x
    return st
# 清空并取基线
s.reset_input_buffer(); time.sleep(0.3)
base_frames=read_frames(0.5)
base=last_status(base_frames)
print("BASE:", base)
enc0 = base["enc"] if base else [0,0,0,0]
# 发送左转90°
s.write(protocol.cmd_rotate(90))
frames=read_frames(4.0)
modes=[]
for cmd,data in frames:
    if cmd==0x81:
        st=protocol.parse_status(data)
        if st and (not modes or modes[-1]!=st["mode"]): modes.append(st["mode"])
after=last_status(frames)
print("MODE SEQUENCE:", modes)
print("AFTER:", after)
if after:
    enc1=after["enc"]
    cpr=2464.0; dia=0.08; lw=(0.130+0.1235)/2.0
    dist=[(enc1[i]-enc0[i])*(math.pi*dia)/cpr for i in range(4)]
    yaw=((dist[1]+dist[3])-(dist[0]+dist[2]))/(4.0*lw)
    print("delta counts:", [enc1[i]-enc0[i] for i in range(4)])
    print("delta dist:", [round(x,4) for x in dist])
    print("estimated yaw deg:", round(math.degrees(yaw),2))
s.close()
