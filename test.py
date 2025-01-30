import serial
import json
import time

# Configure the serial connection (adjust COM port and baud rate)
SERIAL_PORT = "COM3"  # Change to "/dev/ttyUSB0" or "/dev/ttyACM0" for Linux/Mac
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Allow time for the connection to establish
    print(f'Connected to {SERIAL_PORT} at {BAUD_RATE} baud.')
except serial.SerialException as e:
    print(f'Error: {e}')
    exit()

def read_json_from_arduino():
    """Reads and parses JSON data from Arduino serial."""
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()  # Read a line
                print(f"Raw Data: {line}")  # Debugging: print raw data
                
                # Parse JSON data
                try:
                    data = json.loads(line)
                    print('Received JSON Data:', data)  # Processed JSON output
                    
                    # Example: Accessing values from JSON
                    if "temperature" in data:
                        print(f'Temperature: {data['temperature']}°C')
                    if "humidity" in data:
                        print(f'Humidity: {data['humidity']}%')
                
                except json.JSONDecodeError:
                    print('Invalid JSON received, skipping...')
        
        except serial.SerialException as e:
            print(f'Serial error: {e}')
            break
        
        except KeyboardInterrupt:
            print('Exiting...')
            ser.close()
            break

# Run the function
read_json_from_arduino()
