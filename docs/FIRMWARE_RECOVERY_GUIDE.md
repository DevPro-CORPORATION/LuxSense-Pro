# LuxSense Pro — Arduino Uno ATmega328P Hardware Recovery Guide

**Document ID:** DEVPRO-DOC-REC-001  
**Target Hardware:** Arduino Uno R3 / ATmega328P @ 16 MHz  
**Bootloader:** Optiboot v4.4+ (STK500v1 protocol, 115200 baud)  
**Organization:** DevPro-CORP  
**Date:** November 15, 2026  

---

## 1. Overview & Memory Map Realities

The Microchip ATmega328P microcontroller utilizes a single-bank flash memory architecture totaling 32,768 bytes (32 KB). 

```
+-----------------------------------------------------------+ 0x7FFF (32768)
| Optiboot Bootloader (512 Bytes, 0x7E00 - 0x7FFF)          | <-- Protected
+-----------------------------------------------------------+ 0x7DFF
|                                                           |
| Application Firmware Space (31.5 KB, 0x0000 - 0x7DFF)     | <-- Overwritten
| (LuxSense Pro Radiometry Microcode: ~10.6 KB)             |
|                                                           |
+-----------------------------------------------------------+ 0x0000
```

> [!WARNING]
> Because there is only a single 32 KB memory bank, the ATmega328P cannot hold two full firmware images concurrently. Dual-bank automatic A/B firmware rollback is physically impossible on this microcontroller. Never trust any claims of automatic microcontroller rollback on standard 8-bit AVR hardware.

---

## 2. Diagnostics & Incident Preservation

When an update operation does not complete successfully:
1. **Logs Preserved:** LuxSense Pro automatically archives full console logs to:
   ```
   %APPDATA%\DevPro\LuxSensePro\firmware_flash.log
   ```
2. **Settings Untouched:** SQLite databases (`history.db`), user preferences (`settings.json`), and optical calibration profiles (`calibration.json`) are stored on the host PC and are completely isolated from microcontroller flash operations.
3. **Never Blindly Re-flash:** Read the diagnostic log to identify the exact cause (port lock, timeout, communication noise, or physical disconnection) before attempting re-programming.

---

## 3. Step-by-Step Recovery Procedures

### Scenario A: Upload Interrupted or Timed Out (Optiboot Intact)
**Symptom:** Flashing was interrupted by a pulled USB cable or system sleep, or timed out.  
**Condition:** The Optiboot bootloader in high memory (`0x7E00`) is intact and listening.

**Resolution Steps:**
1. Disconnect the USB cable from the Arduino Uno.
2. Wait 5 seconds to discharge on-board filter capacitors.
3. Plug the USB cable back into the PC.
4. Verify in Windows Device Manager under **Ports (COM & LPT)** that the port (e.g., `COM5`) is recognized.
5. In LuxSense Pro Settings, select the **ATmega328P Firmware Center** tab.
6. Check the safety box: *"I understand this writes directly to microcontroller flash memory"*.
7. Click **AUTHORIZE & FLASH FIRMWARE**. The Optiboot bootloader listens for programming instructions during the first 1.5 seconds after power-up and will cleanly accept the new firmware.

---

### Scenario B: avrdude stk500_getsync() Synchronization Failure
**Symptom:** Log displays `avrdude: stk500_getsync() attempt 1 of 10: not in sync: resp=0x00`.  
**Root Causes:**
- Serial port contention (another application like Arduino IDE, Cura, or PuTTY is holding the port).
- The automatic DTR reset capacitor on the Arduino Uno failed to trigger a hardware reset.
- Signal degradation from an unpowered USB hub or faulty USB cable.

**Resolution Steps:**
1. Close all external applications that might communicate with serial devices.
2. Connect the Arduino Uno directly to a motherboard USB port (avoid unpowered external hubs).
3. If auto-reset does not engage, use manual reset timing:
   - Click **AUTHORIZE & FLASH FIRMWARE** in LuxSense Pro.
   - The moment the console displays `Phase 4: Initiating physical flash programming...`, immediately press and release the small **RED RESET button** on the Arduino Uno.
   - This manually enters the Optiboot bootloader mode just as avrdude sends its STK500 sync packets.

---

### Scenario C: Corrupted Bootloader (In-System Programming / ISP Reprogramming)
**Symptom:** Arduino Uno shows no LED activity on pin 13 upon power-up; avrdude fails consistently despite manual reset.  
**Condition:** The 512-byte bootloader section was damaged (e.g. power loss during high-voltage fuse programming or electrical spike).

**Required Equipment:**
- A hardware ISP programmer (e.g., USBasp, AVR ISP mkII), **OR** a spare working Arduino board configured as an "Arduino as ISP".
- 6-pin ICSP ribbon cable or 6 female-to-male jumper wires.

**Pinout Configuration (Arduino Uno ICSP Header):**
```
    ICSP Header (Top View):
    [Pin 1: MISO]  [Pin 2: VCC (+5V)]
    [Pin 3: SCK ]  [Pin 4: MOSI      ]
    [Pin 5: RESET] [Pin 6: GND       ]
```

**Reprogramming Commands (via bundled avrdude):**
1. Connect the programmer to the PC and the target Arduino ICSP header.
2. Open PowerShell in the LuxSense Pro directory.
3. Burn the official Optiboot bootloader:
   ```powershell
   & "C:\Users\AIMLOPS\AppData\Local\Arduino15\packages\arduino\tools\avrdude\8.0.0-arduino1\bin\avrdude.exe" `
       -C "C:\Users\AIMLOPS\AppData\Local\Arduino15\packages\arduino\tools\avrdude\8.0.0-arduino1\etc\avrdude.conf" `
       -v -p m328p -c stk500v1 -P COM4 -b 19200 `
       -e -u `
       -U lock:w:0x3F:m `
       -U efuse:w:0xFD:m `
       -U hfuse:w:0xDE:m `
       -U lfuse:w:0xFF:m `
       -U flash:w:"firmware/build/LuxSense_Arduino.ino.with_bootloader.hex":i `
       -U lock:w:0x0F:m
   ```
4. Once completed, disconnect the ISP programmer and reconnect the Arduino Uno via USB.
5. Launch LuxSense Pro; the board will operate normally.
