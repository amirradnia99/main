import serial
import serial.tools.list_ports
import time

# Configuration
BAUDRATE = 115200
TIMEOUT = 2  # Seconds to wait for a response

def find_at_port():
    """
    Scans available COM/USB ports to find the one that responds to 'AT'.
    Returns the port name (e.g., '/dev/ttyUSB2') or None.
    """
    print("Scanning for AT command port...")
    ports = list(serial.tools.list_ports.comports())
    
    # Filter for likely candidates (USB to Serial adapters)
    # On Raspberry Pi/Linux, these usually show up as ttyUSB*
    candidates = [p.device for p in ports if "USB" in p.device or "COM" in p.device]
    
    for port in candidates:
        try:
            print(f"Testing {port}...", end="", flush=True)
            with serial.Serial(port, BAUDRATE, timeout=1) as ser:
                # Clear any garbage
                ser.reset_input_buffer()
                
                # Send simple AT check
                ser.write(b"AT\r\n")
                
                # Read lines for up to 1 second
                start = time.time()
                while (time.time() - start) < 1.0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if "OK" in line:
                        print(" Found!")
                        return port
            print(" No response.")
        except (OSError, serial.SerialException):
            print(" Busy/Error.")
            pass
            
    return None

def send_at_command(ser, cmd, timeout=TIMEOUT):
    """
    Sends an AT command and reads lines until 'OK' or 'ERROR'.
    Returns the full response text.
    """
    try:
        # Ensure command ends with CR+LF
        full_cmd = cmd + "\r\n"
        ser.write(full_cmd.encode())
        
        response_lines = []
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            # readline() blocks based on the serial timeout setting
            line_bytes = ser.readline()
            
            if not line_bytes:
                continue
                
            line = line_bytes.decode('utf-8', errors='ignore').strip()
            
            # Skip empty lines and the echo of the command itself
            if not line or line == cmd:
                continue
                
            response_lines.append(line)
            
            # Check for standard terminators
            if line == "OK":
                return {"status": "success", "data": response_lines}
            if "ERROR" in line:
                return {"status": "error", "data": response_lines}
                
        return {"status": "timeout", "data": response_lines}
        
    except serial.SerialException as e:
        return {"status": "comm_error", "data": [str(e)]}

def main():
    # 1. Auto-detect the port
    port = find_at_port()
    
    if not port:
        print("Error: Could not find a module responding to AT commands.")
        print("Check your USB connection and power supply.")
        return

    print(f"Connecting to {port}...")
    
    try:
        with serial.Serial(port, BAUDRATE, timeout=1) as ser:
            # 2. Initialize
            # Turn off echo (ATE0) so we don't get our own commands back
            print("\n--- Initialization ---")
            send_at_command(ser, "ATE0")
            
            # Check module info
            resp = send_at_command(ser, "ATI")
            print(f"Module Info: {resp['data']}")

            # Check SIM status
            resp = send_at_command(ser, "AT+CPIN?")
            print(f"SIM Status: {resp['data']}")

            # 3. Main Loop
            print("\n--- Starting Signal Monitor (Ctrl+C to stop) ---")
            while True:
                # Query Signal Quality
                # Response format is +CSQ: <rssi>,<ber>
                result = send_at_command(ser, "AT+CSQ")
                
                if result['status'] == 'success':
                    # Parse the specific line containing +CSQ
                    csq_line = next((line for line in result['data'] if "+CSQ:" in line), None)
                    if csq_line:
                        print(f"Signal: {csq_line}")
                    else:
                        print("Signal: OK (No data)")
                else:
                    print(f"Warning: Command failed ({result['status']})")
                
                time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"\nUnexpected Error: {e}")

if __name__ == "__main__":
    main()