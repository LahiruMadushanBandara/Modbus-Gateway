from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore import ModbusSimulatorContext

device = {
    "co size": 100,
    "di size": 100,
    "hr size": 100,
    "ir size": 100,
}

store = ModbusSimulatorContext(device, None)
context = ModbusServerContext(slaves=store, single=True)

print(">>> Modbus Simulator running on port 5020...")

StartTcpServer(
    context=context,
    address=("0.0.0.0", 5020)
)