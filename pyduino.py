import serial
import serial.tools.list_ports
import json
import time

# Note:
# check_presence() at first run is tied to the inital usb port
# it identified an arduino. It will reserve and check only on that port.
# So you're better off plugging it back to the same port you
# initially used


"""Do not use this module as is unless you want to go through the hassle
of commenting out the json part.
"""

def find_arduino():
    """Find the connected Arduino by checking available serial ports."""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "Arduino" in port.description or "CH340" in port.description \
            or 'USB Serial Port' in port.description:
            return port.device  # Returns something like 'COM3' or '/dev/ttyUSB0'
    return None

def connect_arduino():
    """Attempt to connect to Arduino and return the serial object."""
    while True:
        port = find_arduino()
        if port:
            try:
                print(f"✅ Found Arduino on {port}, connecting...")
                ser = serial.Serial(port, 9600, timeout=1)
                time.sleep(2)  # Wait for Arduino to reset
                print(f"🔌 Connected to Arduino on {port}!")
                return ser
            except serial.SerialException as e:
                print(f"❌ Failed to connect: {e}")
        else:
            print("❌ No Arduino found. Retrying in 2 seconds...")
        
        time.sleep(2)  # Retry every 2 seconds

def read_json_data(ser, db_obj, db_model, context):
    """Continuously reads JSON data from Arduino and save to the databse."""
    with context:
        while True:
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode("utf-8").strip()
                    if line:
                        try:
                            data = json.loads(line)
                            print("📊 Received JSON:", data)

                            # Ignore empty JSON
                            if not any(data.values()):  
                                print("⚠️ Empty JSON received, ignoring...")
                                continue

                            for key, values in data.items():
                                if not values:  # Skip empty node
                                    continue

                                node_id = int(key[-1])  # Get last character (e.g., node1 -> 1)
                                sta = values.get("sta", None)
                                batt = values.get("batt", None)
                                ldr = values.get("ldr", None)

                                if sta is not None and batt is not None and ldr is not None:
                                    status = "ON" if sta == 1 else "OFF"


                                    node = db_model.query.get(node_id)
                                    #if node exists already then update
                                    if node:
                                        node.status = status
                                        node.battery_lvl = batt * 0.0197
                                        node.ldr_res = ldr
                                        try:
                                            db_obj.session.commit() 
                                        except:
                                            return f'There was an error adding node{node_id}'
                                    else:
                                        node = db_model(status=status, battery_lvl=batt, ldr_res=ldr)
                                        try:
                                            db_obj.session.add(node)
                                            db_obj.session.commit() 
                                        except:
                                            return f'There was an error adding node{node_id}'
                                else:
                                    print(f"⚠️ Incomplete data for {key}, skipping...")
                        except json.JSONDecodeError:
                            print(f"⚠️ Invalid JSON received: {line}")
            except serial.SerialException:
                print("❌ Connection lost! Attempting to reconnect...")
                ser.close()
                ser = connect_arduino()  # Reconnect if connection is lost


if __name__ == "__main__":
    try:
        serial_connection = connect_arduino()
        read_json_data(serial_connection)
    except KeyboardInterrupt:
        print('Exiting...')

# #starts the service --mostlikely used same as ngrok was used
# def check_ard():
#     port_controller.start()
