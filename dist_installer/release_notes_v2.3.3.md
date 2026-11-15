# LuxSense Pro v2.3.3 — Critical Hardware & Update Lifecycle Repair

DevPro-CORP is pleased to announce the production release of **LuxSense Pro v2.3.3**, delivering a real-time non-blocking firmware flashing console, complete elimination of post-flash application freezes, targeted process termination safeguards, and detached application relaunch handoffs.

### Key Highlights & Features
- **Real-Time Subprocess Console Streaming:** Implemented a non-blocking threaded queue reader in `FirmwareFlashWorker` with dedicated `\r` (0x0D) and `\n` (0x0A) delimiter handling. `avrdude` write and verify progress bars (`Writing | ###... | 100%`) now stream smoothly to the UI in real time without batching delays.
- **Console Telemetry & Diagnostics:** Added live elapsed timer (`⏱ Elapsed: 00:05.4s`), target board and COM port identification badges, dedicated write/verification progress indicators, syntax-highlighted terminal log viewer with auto-scroll, and instant **Copy Log** and **Save Log** diagnostic export tools.
- **Elimination of Post-Flashing UI Freeze:** Resolved thread contention between the Qt main GUI thread and background serial worker. Latency measurement is now performed exclusively within the background `SerialWorker` thread loop, and `webengine_host.py::getSerialLatency()` queries the cached float with zero serial I/O. Telemetry resumption after flashing is safely scheduled on the main thread with a 1200ms Windows USB-CDC settle guard.
- **Targeted Process Termination Safeguards:** Replaced global image-name process killing with targeted PID-tree termination (`taskkill /F /PID <wait_pid> /T`). The updater never terminates unrelated user applications or system processes.
- **Detached Application Relaunch:** Upgraded application relaunch in `updater/bootstrapper.py` to use Windows `os.startfile(target_exe)` with explicit `cwd=target_dir` and detached subprocess fallback (`DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`), guaranteeing that the application reopens cleanly after update installation.
- **Zero-Fabrication Metrology:** Preserves authentic physical sensor telemetry. Sensor disconnected, offline, and I2C error states are strictly represented as genuine diagnostics without fabricated data.

### Cryptographic Checksums (SHA-256)
```
6fc45250a553c9039b4699a1432992231d370af5b293b87c2fd86b118cbca4d1  LuxSense-Pro-Setup-v2.3.3.exe
99c1d4913b2dbbc063744e1ae892bc617c7a16c1c398156f395292f52d0b1c09  LuxSense-Pro-v2.3.3-portable.zip
2c869b53d5029c5ef5b6045b62a14710dad0c95d377932028537810a6d3d79ca  updater.exe
7e411e6431ad12bebe634072122a55141a677aa2c806ca2919a6ef658deea10a  firmware-manifest.json
0d252ba9d2fbe909055ffece802cd815879001916b41587d278c33ba19cc5c23  LuxSense_Arduino.ino.hex
```

*Note: Firmware flashing is strictly opt-in and requires explicit operator authorization in Settings. LuxSense Pro never automatically flashes microcontroller hardware.*
