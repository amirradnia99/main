# Quectel-EC200U-Signal-Monitor

A Python-based telemetry and signal monitoring tool for Quectel EC200U and similar AT-command cellular modules. The utility automatically detects available USB/COM ports, identifies the correct AT interface, executes diagnostic AT commands, and continuously monitors signal quality parameters such as RSSI and BER using `AT+CSQ`.

---

## Features

- Automatic detection of active AT command serial port  
- Clean and structured AT command execution  
- Device identification through `ATI`  
- SIM card status check via `AT+CPIN?`  
- Continuous signal-level monitoring (`AT+CSQ`)  
- Graceful handling of timeouts and serial exceptions  
- Fully extensible for additional AT commands and telemetry functions  

---

## Requirements

- Python 3.8+
- EC200U module (or any AT-compatible LTE/4G module)
- Required Python library:

```bash
pip install pyserial
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/Quectel-EC200U-Signal-Monitor.git
cd Quectel-EC200U-Signal-Monitor
```

Run the script:

```bash
python EC200U\ Telemetry\ Logger.py
```

(Ensure the filename matches your environment.)

---

## Sample Output

```text
Scanning for AT command port...
Testing /dev/ttyUSB2... Found!
Connecting to /dev/ttyUSB2...

--- Initialization ---
Module Info: ['Quectel EC200U', 'Revision XYZ']
SIM Status: ['+CPIN: READY']

--- Starting Signal Monitor (Ctrl+C to stop) ---
Signal: +CSQ: 19,99
Signal: +CSQ: 20,99
...
```

---

## Extending the Tool

### Network registration
```bash
AT+CREG?
```

### Operator information
```bash
AT+COPS?
```

### Programmatically send AT commands
```python
send_at_command(ser, "AT+<COMMAND>")
```

You can extend functionality by adding new AT commands or integrating logging, cloud upload, or LTE diagnostics.

---

## Troubleshooting

**No AT port detected**  
- Ensure the EC200U module is powered.  
- On Linux, confirm the device appears under `/dev/ttyUSB*`.  
- On Windows, confirm it appears under `COMx`.

**Timeout or no response**  
- Check cable quality.  
- Try increasing the serial timeout.  

**AT commands return ERROR**  
- Ensure SIM is inserted and unlocked.  
- Verify antenna is connected.  

---

## File Overview

| File                          | Purpose                                                             |
|-------------------------------|---------------------------------------------------------------------|
| `EC200U Telemetry Logger.py` | Main script for port detection, AT communication, and monitoring.   |

---

## License

This project is distributed under the MIT License.
