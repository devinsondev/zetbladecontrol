"""ZET Blade protocol (adapted from OpenRGB GPL-2.0-or-later)."""
import time
import sys
import re
import hid

VID, PID = 0x2EA8, 0x2125
SKIPS = [1,17,18,19,20,75,77,78,79,83,85,96,98,100,108,109,111,112,113,116,123,125]
MODES = dict(Static=0x02,Breathing=0x03,Reactive=0x04,Raindrop=0x05,Ripple=0x06,
             Laser=0x07,Waves=0x08,Rain=0x09,Spectrum=0x0A,Wave=0x0B,
             Vortex=0x0C,Center=0x0D,Traffic=0x0E,Cross=0x0F,Gradient=0x15,Off=0x01)
PALETTE = dict(Red=1,Green=2,Blue=3,Yellow=4,Magenta=5,Cyan=6,White=7)
KEYS = (["Esc"]+["F"+str(i) for i in range(1,13)]+["PrtSc","Scroll","Pause"]
        +["Tilde"]+list("1234567890")+["-","=","Backspace","Ins","Home","PgUp","Num","Num/","Num*","Num-"]
        +["Tab"]+list("QWERTYUIOP")+["[","]","Backslash","Del","End","PgDn","Num7","Num8","Num9","Num+"]
        +["Caps"]+list("ASDFGHJKL")+[";","Quote","Enter","Num4","Num5","Num6"]
        +["LShift"]+list("ZXCVBNM")+[",",".","/","RShift","Up","Num1","Num2","Num3","NumEnter"]
        +["LCtrl","Win","LAlt","Space","RAlt","Fn","Menu","RCtrl","Left","Down","Right","Num0","Num."])
assert len(KEYS) == 104

def validate_color(color):
    if not isinstance(color, str) or re.fullmatch(r"#[0-9A-Fa-f]{6}", color) is None:
        raise ValueError("Color must be #RRGGBB")
    return color.upper()

def level(n):
    n=int(n)
    if n not in range(5):
        raise ValueError("Expected 0..4")
    return n

def header(mode, speed, brightness, color):
    p=bytearray(65)
    p[0:3]=bytes([4,0xAE,1])
    p[5:9]=bytes([mode,level(speed),level(brightness),color])
    return p

def effect_packet(name, color, speed, brightness, rainbow=False):
    if name not in MODES:
        raise ValueError("Unknown mode")
    if name=="Static":
        code=PALETTE[color]-1
    elif name in ("Rain","Spectrum","Wave","Vortex","Center","Traffic","Cross","Gradient","Off") or rainbow:
        code=0
    else:
        code=PALETTE[color]
    return bytes(header(MODES[name],speed,brightness,code))

def custom_packets(colors, brightness):
    if len(colors)!=104:
        raise ValueError("104 colors required")
    records=[]
    for i,color in enumerate(colors):
        position=i
        for skip in SKIPS:
            if skip<=position:
                position+=1
            else:
                break
        records.append(bytes([position+0x80])+bytes.fromhex(validate_color(color)[1:]))
    packets=[]
    for start in range(0,104,12):
        p=header(0x1C,2,brightness,0xFF)
        offset=9
        for record in records[start:start+12]:
            p[offset:offset+4]=record
            offset+=4
        if start+12>=104:
            p[offset]=0xFF
        packets.append(bytes(p))
    return packets

class BladeDevice:
    def __init__(self):
        self.dev=None
    def connect(self):
        devices=[d for d in hid.enumerate(VID,PID)
                 if d.get("usage_page")==0xFF00 and d.get("interface_number")==1]
        if not devices:
            raise RuntimeError("ZET Blade FF00 interface not found; close OpenRGB and vendor software")
        self.close()
        self.dev=hid.device()
        try:
            self.dev.open_path(devices[0]["path"])
        except Exception:
            # Failed open must not leave a fake "connected" handle behind.
            self.close()
            raise
    def send(self, packets):
        if self.dev is None:
            raise RuntimeError("Connect first")
        for packet in packets:
            # OpenRGB uses 65-byte buffers, including Report ID 0x04.
            if len(packet) != 65:
                raise ValueError("ZET Blade HID packet must be 65 bytes including Report ID")
            sent = self.dev.write(packet)
            # On Windows, HIDAPI returns the 64-byte OutputReportByteLength
            # reported by this keyboard, even for a 65-byte application buffer.
            windows_report_written = sys.platform == "win32" and sent == 64
            if sent != len(packet) and not windows_report_written:
                raise IOError("HID write incomplete: %s/%s" % (sent, len(packet)))
            time.sleep(0.012)
    def close(self):
        if self.dev:
            self.dev.close()
            self.dev=None
