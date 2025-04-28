import serial
import serial.tools.list_ports
import json
import time


"""
    Interface between the flask web server
    and the Arduino device.
"""

serial_connection = None
flag = True  # necessary to use a global flag to enable TDD


def find_arduino():
    """Find the connected Arduino by checking available serial ports."""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if (
            "Arduino" in port.description
            or "CH340" in port.description
            or "USB Serial Port" in port.description
        ):
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
            print("❌ No Arduino found. Retrying...")

        time.sleep(2.5)  # Retry every 2.5 seconds


def read_json_data(db_obj, db_model, app):
    """Continuously reads JSON data from Arduino and saves to the database."""
    global serial_connection
    serial_connection = connect_arduino()
    with app.app_context():
        global flag  # noqa
        while flag:
            # catches serial errors
            try:
                if serial_connection.in_waiting > 0:
                    line = serial_connection.readline().decode("utf-8").strip()
                    if line:
                        # catches json errors
                        try:
                            # read json and save to the database
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

                                if sta is None and batt is None and ldr is None:
                                    print(f"⚠️ Incomplete data for {key}, skipping...")
                                    continue
                                status = "ON" if sta == 1 else "OFF"

                                # catches database errors
                                try:
                                    node = db_model.query.get(node_id)

                                    # if node exists already then update
                                    if node:
                                        node.status = status
                                        node.battery_lvl = round(batt * 0.0197, 2)
                                        node.ldr_res = ldr
                                    else:
                                        node = db_model(
                                            id=node_id,
                                            status=status,
                                            battery_lvl=batt,
                                            ldr_res=ldr,
                                        )
                                        db_obj.session.add(node)
                                    db_obj.session.commit()
                                except Exception as e:
                                    db_obj.session.rollback()
                                    print(
                                        f"FATAL! database error while processing node{node_id}: {e}"
                                    )
                        except json.JSONDecodeError:
                            print(f"⚠️ Invalid JSON received: {line}")
            except serial.SerialException:
                print("❌ Connection lost! Attempting to reconnect...")
                serial_connection.close()
                serial_connection = connect_arduino()  # Reconnect if connection is lost


# use this for imports
def start_pyduino(db_obj, db_model, app):
    read_json_data(db_obj, db_model, app)
