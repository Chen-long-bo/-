import serial, time
ports = [
    ("COM5", 115200),
    ("COM7", 9600),
    ("COM8", 9600),
]
for name, baud in ports:
    print("== try open", name, baud)
    try:
        s = serial.Serial(name, baud, timeout=0.5)
        print("  OPEN OK:", s.name, "DSR", s.dsr, "CTS", s.cts, "CD", s.cd)
        # 尝试读一点数据，超时也没关系
        try:
            data = s.read(64)
            print("  read bytes:", len(data), repr(data[:64]))
        except Exception as e:
            print("  read error:", repr(e))
        s.close()
        print("  closed")
    except Exception as e:
        print("  OPEN FAIL:", repr(e))
