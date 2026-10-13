# ZET Blade Control

Experimental Windows RGB editor for ZET Blade (USB VID 2EA8 / PID 2125, revision 0103).

## Install & run

Install Python 3.10 or newer. Open PowerShell in the project folder:

```powershell
py -m pip install -r requirements.txt
py app.py
```

Close OpenRGB and any ZET configuration utility before connecting. Press **Connect USB** and use either the built-in effects panel or the 104-key editor. Choose a paint color, click the keys to recolor them in the preview, and press **Apply 104-key RGB profile** to write once. You can save/load JSON profiles.

## Supported controls

- Built-in animation modes, palette (7 hardware colors), speed 0–4, brightness 0–4.
- Individual 24-bit colors for 104 keys and reusable JSON profiles.
- No background RGB streaming, firmware modifications or driver replacement.

## Warnings and limitations

**Experimental hardware access: physical device compatibility has not been tested yet.** The controller writes HID packets on the vendor-defined page FF00, interface 1. Custom profiles may be saved to flash memory inside the keyboard; do not repeatedly apply profiles in a loop or attempt real-time animations. Close other RGB apps first. The 104-key mapping assumes the OpenRGB ZET Blade Optical arrangement and may vary on other revisions.

Uses protocol details and algorithmic adaptation from [OpenRGB's ZET Blade Optical controller](https://github.com/CalcProgrammer1/OpenRGB/tree/master/Controllers/ZETKeyboardController) (GPL-2.0-or-later). This code is released under GPL-2.0-or-later.
