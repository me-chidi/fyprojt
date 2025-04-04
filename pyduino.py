import serial
import serial.tools.list_ports
import json
import time



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
    # global serial_connection
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
            print("❌ No Arduino found. Retrying...")
        
        time.sleep(2.5)  # Retry every 2.5 seconds

def read_json_data(db_obj, db_model, app):
    """Continuously reads JSON data from Arduino and saves to the database."""
    global serial_connection
    serial_connection = connect_arduino()
    with app.app_context():
        while True:
            try:
                if serial_connection.in_waiting > 0:
                    line = serial_connection.readline().decode("utf-8").strip()
                    if line:
                        try:
                            #read json and save to the database
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
                                sta = values.get('sta', None)
                                batt = values.get('batt', None)
                                ldr = values.get('ldr', None)

                                if sta is not None and batt is not None and ldr is not None:
                                    status = "ON" if sta == 1 else "OFF"

                                    node = db_model.query.get(node_id)
                                    #if node exists already then update
                                    if node:
                                        node.status = status
                                        node.battery_lvl = round(batt * 0.0197, 2)
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
                serial_connection.close()
                serial_connection = connect_arduino()  # Reconnect if connection is lost

#new main fxn for imports
def start_pyduino(db_obj, db_model, app):
    read_json_data(db_obj, db_model, app)


if __name__ == "__main__":
    try:
        serial_connection = connect_arduino()
        read_json_data(serial_connection)
    except Exception as e:
        print(f'Error!: {e}')

# #starts the service --mostlikely used same as ngrok was used
# def check_ard():
#     port_controller.start()

#consider making all this a class
# for better packing