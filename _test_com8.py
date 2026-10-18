import serial
for name in ["COM8", "COM7"]:
    for attempt in range(3):
        try:
            s = serial.Serial(name, 9600, timeout=2)
            print(name, "OPEN OK", attempt, s.name)
            data = s.read(32)
            print("  read:", len(data), data)
            s.close()
            break
        except serial.SerialException as e:
            print(name, "attempt", attempt, "FAIL", repr(e))
            import errno
            print("  args:", e.args)
        except Exception as e:
            print(name, "attempt", attempt, "ERR", type(e), repr(e))
