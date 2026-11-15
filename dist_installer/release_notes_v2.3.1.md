# LuxSense Pro v2.3.1 — Final Production Bug Hunt, UI Refinement & Hardware Validation

DevPro-CORP is pleased to announce the production release of **LuxSense Pro v2.3.1**, delivering repository-wide defect resolution, Clean Metrology Light Mode contrast enhancements, multi-board AVR flashing support (Arduino Uno & Nano), and collision-safe update rollback mechanics.

### Key Highlights & Features
- **Multi-Board AVR Flashing Support:** Extended the Firmware Update Center and cryptographic verification engine to support both Arduino Uno R3 and Arduino Nano (ATmega328P 16MHz) hardware targets, including dynamic FQBN configuration and baud rate selection.
- **Clean Metrology Light Mode Polish:** Eradicated hardcoded dark backgrounds in the disconnected hardware banner, mapped `text-zinc-600` in the light-mode stylesheet to `#475569`, and adapted all Apache ECharts visualizations (including the photopic responsivity spectral comparison chart) for seamless real-time light/dark theme switching.
- **Serial Worker Shutdown Latency Resolution:** Re-ordered `SerialWorker.stop()` to close the active COM port prior to calling `wait()`, eliminating a 2-second blocking delay on exit or disconnect.
- **Updater Bootstrapper Directory Collision Safeguards:** Configured `dirs_exist_ok=True` in `updater/bootstrapper.py` backup creation and rollback mechanisms to prevent Windows `FileExistsError` during locked file recovery.
- **Portable Distribution Asset Resolution:** Added `find_portable_asset()` to the update subsystem for direct automated discovery of standalone portable distributions.
- **Zero-Fabrication Metrology:** Rigorously preserves all physical measurement verification guardrails; zero synthetic or fabricated data is ever emitted when sensors are disconnected or experiencing I2C bus errors.

### Cryptographic Checksums (SHA-256)
```
d6aedeccd9c854afb012f9ccc4edf8e9e7582e2ea9f76ee383ce21384a34a157  LuxSense-Pro-Setup-v2.3.1.exe
0c37de42fb575328a40da81f9c2e29e417466a8f1216a10ad349bcd055a828ae  LuxSense-Pro-v2.3.1-portable.zip
98d518452848267880655161580189ced47c5889d6b74477e8ec0b66b82a9554  updater.exe
17ce3ee09e2bd2ed73e90dfd014ca808436314eb3387607aced2e33f7814986f  firmware-manifest.json
0d252ba9d2fbe909055ffece802cd815879001916b41587d278c33ba19cc5c23  LuxSense_Arduino.ino.hex
```

*Note: Firmware flashing is strictly opt-in and requires explicit operator authorization in Settings. LuxSense Pro never automatically flashes microcontroller hardware.*
