from flask import Flask, request, jsonify
from pymodbus.client import ModbusTcpClient
import threading
import time

app = Flask(__name__)

# Current state
state = "IDLE"

# Modbus connection to simulator (your laptop IP)
MODBUS_HOST = '192.168.1.50'  # ← Replace with your laptop IP
MODBUS_PORT = 502
SLAVE_ID    = 1

def get_modbus_client():
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    client.connect()
    return client

# Modbus bit operations
def set_bit(client, bit, value):
    result = client.write_coil(bit, value, unit=SLAVE_ID)
    if result.isError():
        print(f">>> ERROR writing bit {bit}")
    else:
        print(f">>> Modbus: bit {bit} set to {value} ✅")

def read_bit(client, bit):
    result = client.read_coils(bit, 1, unit=SLAVE_ID)
    if result.isError():
        print(f">>> ERROR reading bit {bit}")
        return False
    return result.bits[0]

# Emergency Start Sequence
def emergency_start_sequence():
    global state

    print("\n>>> [1] Setting MANUAL mode (MANUAL_LOC bit 3 = 1)")
    client = get_modbus_client()
    set_bit(client, 3, True)
    time.sleep(1)

    print(">>> [2] Waiting for CONTROL_EN (bit 5)...")
    for _ in range(10):
        if read_bit(client, 5):
            print(">>> [2] CONTROL_EN confirmed ✅")
            break
        time.sleep(1)

    print(">>> [3] Activating ALL SPEECH (bit 10 = 1)")
    set_bit(client, 10, True)

    state = "EMERGENCY_ACTIVE"
    print(">>> STATE: EMERGENCY_ACTIVE")
    client.close()

# Emergency Stop Sequence
def emergency_stop_sequence():
    global state

    state = "WAITING"
    print("\n>>> Waiting 60 seconds before shutdown...")
    time.sleep(60)

    client = get_modbus_client()

    print(">>> [1] Deactivating ALL SPEECH (bit 10 = 0)")
    set_bit(client, 10, False)
    time.sleep(1)

    print(">>> [2] Returning to AUTO mode (MANUAL_LOC bit 3 = 0)")
    set_bit(client, 3, False)

    state = "IDLE"
    print(">>> STATE: IDLE - System back to AUTO ✅")
    client.close()

# Flask API
@app.route('/event', methods=['POST'])
def handle_event():
    global state
    data  = request.json
    event = data.get('event')

    print(f"\n>>> Event received: {event}")

    if event == 'EMERGENCY_START':
        if state == "IDLE":
            thread = threading.Thread(target=emergency_start_sequence)
            thread.start()
        else:
            print(f">>> Ignored - current state is {state}")

    elif event == 'EMERGENCY_STOP':
        if state == "EMERGENCY_ACTIVE":
            thread = threading.Thread(target=emergency_stop_sequence)
            thread.start()
        else:
            print(f">>> Ignored - current state is {state}")

    return jsonify({'status': 'ok', 'state': state})

if __name__ == '__main__':
    print(">>> ARA Fire Modbus Bridge Starting...")
    print(f">>> Connecting to Modbus at {MODBUS_HOST}:{MODBUS_PORT}")
    print(">>> State: IDLE")
    app.run(host='0.0.0.0', port=5000)