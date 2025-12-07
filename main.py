import serial
import serial.tools.list_ports
import time
import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Configuration
BAUDRATE = 115200
TIMEOUT = 2
SIMULATION_MODE = True  # Set to False when real hardware arrives

app = FastAPI(title="EC200U Cellular Monitor API")

# Enable CORS so the browser can talk to this script
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SerialManager:
    def __init__(self):
        self.ser = None
        self.simulation_data = {
            'signal_strength': 20,
            'connected': False,
            'port': None
        }

    def find_at_port(self):
        """Scans for a port responding to AT commands."""
        if SIMULATION_MODE:
            # Simulate finding a port
            simulated_ports = ["COM3", "/dev/ttyUSB0", "/dev/ttyACM0"]
            print("🔍 Simulation: Scanning for ports...")
            time.sleep(1)  # Simulate scan time
            port = random.choice(simulated_ports)
            print(f"✅ Simulation: Found {port}")
            return port
        
        # Real hardware scanning
        print("Scanning for AT command port...")
        ports = list(serial.tools.list_ports.comports())
        candidates = [p.device for p in ports if "USB" in p.device or "COM" in p.device]
        
        for port in candidates:
            try:
                print(f"Testing {port}...")
                with serial.Serial(port, BAUDRATE, timeout=1) as temp_ser:
                    temp_ser.reset_input_buffer()
                    temp_ser.write(b"AT\r\n")
                    time.sleep(0.5)
                    resp = temp_ser.read_all().decode(errors='ignore')
                    if "OK" in resp:
                        print(f"✅ Found device on {port}")
                        return port
            except Exception as e:
                print(f"❌ {port} failed: {e}")
                pass
        return None

    def connect(self):
        if SIMULATION_MODE:
            print("🔌 Simulation: Connecting to virtual modem...")
            time.sleep(1)  # Simulate connection time
            self.simulation_data['connected'] = True
            self.simulation_data['port'] = "COM3 (Simulation)"
            return {
                "status": "connected", 
                "port": self.simulation_data['port'],
                "message": "Connected to simulated EC200U modem"
            }

        # Real connection logic
        if self.ser and self.ser.is_open:
            return {"status": "already_connected", "port": self.ser.port}

        port = self.find_at_port()
        if not port:
            raise HTTPException(status_code=404, detail="No AT module found")

        try:
            self.ser = serial.Serial(port, BAUDRATE, timeout=TIMEOUT)
            self.send_at("ATE0")  # Turn off echo
            return {"status": "connected", "port": port}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def disconnect(self):
        if SIMULATION_MODE:
            print("🔌 Simulation: Disconnecting...")
            self.simulation_data['connected'] = False
            return {"status": "disconnected", "message": "Simulated modem disconnected"}
            
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None
        return {"status": "disconnected"}

    def send_at(self, cmd):
        if SIMULATION_MODE:
            # Simulate realistic responses
            if cmd == "AT":
                return {"status": "success", "data": ["OK"]}
            elif cmd == "ATE0":
                return {"status": "success", "data": ["OK"]}
            elif cmd == "ATI":
                return {"status": "success", "data": ["EC200U", "Revision: LTE_1.0", "OK"]}
            elif cmd == "AT+CPIN?":
                return {"status": "success", "data": ["+CPIN: READY", "OK"]}
            elif cmd == "AT+CSQ":
                # Simulate signal fluctuations
                self.simulation_data['signal_strength'] = max(5, min(31, 
                    self.simulation_data['signal_strength'] + random.randint(-2, 2)))
                ber = random.randint(0, 2)
                return {
                    "status": "success", 
                    "data": [f"+CSQ: {self.simulation_data['signal_strength']},{ber}", "OK"]
                }
            else:
                return {"status": "error", "data": ["ERROR"]}

        # Real command handling
        if not self.ser or not self.ser.is_open:
            raise HTTPException(status_code=400, detail="Device not connected")

        try:
            self.ser.reset_input_buffer()
            full_cmd = cmd + "\r\n"
            self.ser.write(full_cmd.encode())
            
            response_lines = []
            start_time = time.time()
            
            while (time.time() - start_time) < TIMEOUT:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line or line == cmd:
                        continue
                    response_lines.append(line)
                    if line == "OK":
                        return {"status": "success", "data": response_lines}
                    if "ERROR" in line:
                        return {"status": "error", "data": response_lines}
            return {"status": "timeout", "data": response_lines}
            
        except serial.SerialException as e:
            self.disconnect()
            raise HTTPException(status_code=500, detail=f"Communication Error: {str(e)}")

serial_manager = SerialManager()

# --- API Routes ---
@app.post("/connect")
def connect_device():
    return serial_manager.connect()

@app.post("/disconnect")
def disconnect_device():
    return serial_manager.disconnect()

@app.get("/status")
def get_full_status():
    if SIMULATION_MODE and not serial_manager.simulation_data['connected']:
        raise HTTPException(status_code=400, detail="Not connected")
    
    if not SIMULATION_MODE and (not serial_manager.ser or not serial_manager.ser.is_open):
        raise HTTPException(status_code=400, detail="Not connected")
    
    try:
        return {
            "info": serial_manager.send_at("ATI"),
            "sim": serial_manager.send_at("AT+CPIN?"),
            "signal": serial_manager.send_at("AT+CSQ")
        }
    except Exception as e:
        return {"error": str(e)}