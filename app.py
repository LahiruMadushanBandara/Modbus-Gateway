from flask import Flask, request, jsonify
from pymodbus.client import ModbusTcpClient
import threading
import time

app = Flask(__name__)

state = "IDLE"

MODBUS_HOST = '192.168.1.50'
MODBUS_PORT = 502
SLAVE_ID = 1

def get_modbus_client():
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    client.connect()
    return client

def set_bit(client, bit, value):
    result = client.write_coil(bit, value, unit=SLAVE_ID)
    if result.isError():
        print(">>> ERROR writing bit " + str(bit))
    else:
        print(">>> Modbus: bit " + str(bit) + " set to " + str(value))

def read_bit(client, bit):
    result = client.read_coils(bit, 1, unit=SLAVE_ID)
    if result.isError():
        print(">>> ERROR reading bit " + str(bit))
        return False
    return result.bits[0]

def emergency_start_sequence():
    global state
    client = get_modbus_client()

    print(">>> [1] Setting MANUAL mode bit 3 = 1")
    set_bit(client, 3, True)
    time.sleep(1)

    print(">>> [2] Waiting for CONTROL_EN bit 5...")
    for _ in range(10):
        if read_bit(client, 5):
            print(">>> [2] CONTROL_EN confirmed")
            break
        time.sleep(1)

    print(">>> [3] Activating ALL SPEECH bit 10 = 1")
    set_bit(client, 10, True)

    state = "EMERGENCY_ACTIVE"
    print(">>> STATE: EMERGENCY_ACTIVE")
    client.close()

def emergency_stop_sequence():
    global state
    state = "WAITING"

    print(">>> Waiting 60 seconds...")
    time.sleep(60)

    client = get_modbus_client()

    print(">>> [1] Deactivating ALL SPEECH bit 10 = 0")
    set_bit(client, 10, False)
    time.sleep(1)

    print(">>> [2] Returning to AUTO mode bit 3 = 0")
    set_bit(client, 3, False)

    state = "IDLE"
    print(">>> STATE: IDLE - System back to AUTO")
    client.close()

@app.route('/event', methods=['POST'])
def handle_event():
    global state
    data = request.json
    event = data.get('event')

    print(">>> Event received: " + str(event))

    if event == 'EMERGENCY_START':
        if state == "IDLE":
            thread = threading.Thread(target=emergency_start_sequence)
            thread.start()
        else:
            print(">>> Ignored - current state is " + state)

    elif event == 'EMERGENCY_STOP':
        if state == "EMERGENCY_ACTIVE":
            thread = threading.Thread(target=emergency_stop_sequence)
            thread.start()
        else:
            print(">>> Ignored - current state is " + state)

    return jsonify({'status': 'ok', 'state': state})

if __name__ == '__main__':
    print(">>> ARA Fire Modbus Bridge Starting...")
    print(">>> State: IDLE")
    app.run(host='0.0.0.0', port=5000)