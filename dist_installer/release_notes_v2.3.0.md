# LuxSense Pro v2.3.0 — Unified Software & Microcontroller Firmware Update Architecture

DevPro-CORP is pleased to announce the production release of **LuxSense Pro v2.3.0**, introducing an industrial-grade unified software and physical microcontroller firmware update architecture.

### Key Highlights & Features
- **Dedicated ATmega328P Firmware Update Center:** Embedded sub-tab in Settings with real-time MCU status, 32 KB flash memory gauge, signature verification badges, and live diagnostic terminal.
- **Ed25519 Cryptographic Microcode Validation:** Hardware authority public-key signature verification prevents malicious, corrupted, or incompatible firmware execution.
- **Strict Opt-In Firmware Security:** Microcontroller flashing requires explicit operator authorization via confirmation checkboxes; software updates never trigger automated flashing.
- **Safe 5-Phase Flashing State Machine:** Pre-flight validation -> graceful telemetry teardown -> serial port release -> programmer invocation (`arduino-cli` / `avrdude`) -> post-flash bootloader delay -> handshake query (`ID:GY30_LUX_PRO_2026`) & BH1750 probe -> telemetry resumption.
- **Single-Bank ATmega328P Recovery:** Complete documentation and in-app modal covering Optiboot 1.5s power-cycle recovery and 6-pin ICSP header ISP recovery.
- **Dynamic In-App Update Center:** Reliable update detection for Stable and Beta channels, explicit "Up to Date" notifications, and meaningful error diagnostics.
- **Permanent Release Policy Compliance:** Includes Windows Setup Installer, Zero-Install Portable ZIP, Standalone Updater Bootstrapper, and Cryptographic Manifests.

### Cryptographic Checksums (SHA-256)
```
ec43959563434ba3ab008a1277e4ff0136e6f876e7370733122d79a7129fc6cf  LuxSense-Pro-Setup-v2.3.0.exe
992f5741ef8d36cca9d49136411f5549a53cb16963d9ff3fa65f55a3c63645f5  LuxSense-Pro-v2.3.0-portable.zip
071aee20e59eeb5188b04235f5aaf9e6fb4089c58fdbb2ee3977707ce7a77aa4  updater.exe
b47d2b7dde889a4f2c491272a6955422e5aea3c7eee05309b9758487d4ff6844  firmware-manifest.json
0d252ba9d2fbe909055ffece802cd815879001916b41587d278c33ba19cc5c23  LuxSense_Arduino.ino.hex
```

*Note: Firmware flashing is strictly opt-in and requires explicit operator authorization in Settings. LuxSense Pro never automatically flashes microcontroller hardware.*
