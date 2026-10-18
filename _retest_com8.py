import serial
for name, baud in [("COM8", 9600), ("COM7", 9600)]:
    print("== try open", name)
    try:
        s = serial.Serial(name, baud, timeout=1.0)
        print("  OPEN OK:", s.name, "DSR", s.dsr, "CTS", s.cts, "CD", s.cd)
        try:
            data = s.read(64)
            print("  read bytes:", len(data), repr(data[:64]))
        except Exception as e:
            print("  read error:", repr(e))
        s.close()
        print("  closed")
    except Exception as e:
        print("  OPEN FAIL:", repr(e))
