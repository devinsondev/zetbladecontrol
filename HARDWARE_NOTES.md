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
- **HID control is still experimental** on the target hardware: seeing a keyboard already lit green is *not proof* that a previous write changed its state.
- Next step: use the app to select a distinctly different built-in static color, then test custom RGB, making only intentional manual writes.
- Firmware may persist custom colors to nonvolatile memory: avoid high-frequency updates and automatic animation streaming.

## Application

- App and tests: [PR #1](https://github.com/devinsondev/zetbladecontrol/pull/1).
- Python + Tkinter + HIDAPI.
- Controls built-in effects and offers a 104-key RGB editor with JSON profile storage.
- Physical hardware behavior requires manual testing before being declared supported.

## Publication guidelines

Keep this public repository safe for distribution. Document USB **VID/PID, interfaces, protocol bytes and software requirements only**, never per-computer device instance IDs or personally identifying logs.
