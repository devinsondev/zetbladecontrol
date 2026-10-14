# ZET Blade Control

Experimental Windows RGB editor for ZET Blade (USB VID 2EA8 / PID 2125, revision 0103).

## Install & run

Install Python 3.10 or newer. Open PowerShell in the project folder:

```powershell
py -m pip install -r requirements.txt
py app.py
```

Close OpenRGB and any ZET configuration utility before starting. The app **connects to ZET Blade automatically**, retrying every 3 seconds if the keyboard is missing. Built-in effects, colors, speed and brightness **apply automatically** when you change a control. The app waits 350 ms after the last change and limits writes to one per second; it does not send an initial effect on launch.

For custom per-key RGB, choose a paint color, click keys to recolor them in the preview, and press **Apply 104-key RGB profile** once. You can save/load JSON profiles. Custom profiles are never auto-sent.

## Supported controls

- Built-in animation modes, palette (7 hardware colors), speed 0–4, brightness 0–4, with debounced auto-apply.
- USB auto-connection and periodic retry if the keyboard is initially missing.
- Individual 24-bit colors for 104 keys and reusable JSON profiles (manual Apply).
- No background RGB streaming, firmware modifications or driver replacement.

## Warnings and limitations

**Experimental hardware access: physical device compatibility has not been tested yet.** The controller writes HID packets on the vendor-defined page FF00, interface 1. Built-in effect changes and custom profiles may be saved to flash memory inside the keyboard; avoid rapid/repetitive adjustments, repeatedly applying profiles in a loop, or attempting real-time animations. Close other RGB apps first. The 104-key mapping assumes the OpenRGB ZET Blade Optical arrangement and may vary on other revisions.

Uses protocol details and algorithmic adaptation from [OpenRGB's ZET Blade Optical controller](https://github.com/CalcProgrammer1/OpenRGB/tree/master/Controllers/ZETKeyboardController) (GPL-2.0-or-later). This code is released under GPL-2.0-or-later.
