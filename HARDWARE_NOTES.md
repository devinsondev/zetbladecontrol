# ZET Blade — USB/HID compatibility notes

These notes contain **only generic device and protocol data** for developers. Do not commit user names, individual USB instance paths, serial numbers, screenshots containing account information, diagnostic logs or private machine details.

## Supported candidate device

- Product family: ZET Blade (not Blade 2); compatibility with variants is experimental.
- USB vendor ID: `0x2EA8`; product ID: `0x2125`.
- One tested hardware revision reports `REV_0103`.
- USB is composite with interfaces `MI_00` and `MI_01`.
- Vendor-defined HID collection: **interface `MI_01`, collection `COL03`**, usage page `0xFF00`, usage `0x0000`.
- Windows class drivers include `HidUsb` and `kbdhid`; no third-party USB driver replacement needed.

## HID report probe

A read-only Windows `HidP_GetCaps` probe returned:

```text
UsagePage: 0xFF00
Usage: 0x0000
Output bytes: 64
Feature bytes: 0
```

OpenRGB uses a 65-byte application buffer **including Report ID** in its HIDAPI implementation. Windows HID APIs can expose report sizes differently. Carefully validate lengths before adapting packet writes.

## Protocol and current validation status

- Reference: [OpenRGB ZET Blade Optical controller](https://github.com/CalcProgrammer1/OpenRGB/tree/master/Controllers/ZETKeyboardController), GPL-2.0-or-later.
- Relevant commands in reference implementation: report ID `04`, RGB command `AE`, custom mode `1C`; seven-color built-in palette and 104-key layout.
- **HID control is still experimental** on the target hardware. A first user test observed physical changes with the built-in Static effect; custom per-key RGB is not yet confirmed.
- The Windows device reports 64 output bytes to HIDAPI for a 65-byte application packet (including Report ID); the controller tolerates that response while rejecting other short writes.
- Next step: confirm several distinct built-in static colors, then manually test custom RGB once.
- Firmware may persist built-in effects and custom colors to nonvolatile memory: avoid high-frequency writes and automatic animation streaming.

## Application

- App and tests: [PR #1](https://github.com/devinsondev/zetbladecontrol/pull/1).
- Python + Tkinter + HIDAPI.
- Automatically connects at startup (and retries every 3 seconds if absent); opening the app does not automatically write an effect.
- Automatically applies built-in effects on user changes with a 350 ms debounce and a minimum 1-second gap between successful writes.
- The 104-key RGB editor retains **manual Apply** and JSON profile storage; it never streams per-key changes.
- Full hardware compatibility still requires manual testing before being declared supported.

## Publication guidelines

Keep this public repository safe for distribution. Document USB **VID/PID, interfaces, protocol bytes and software requirements only**, never per-computer device instance IDs or personally identifying logs.
