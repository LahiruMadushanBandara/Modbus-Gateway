from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore import ModbusDeviceContext
from pymodbus.datastore import ModbusSequentialDataBlock

store = ModbusDeviceContext(
    di=ModbusSequentialDataBlock(1, [0]*100),
    co=ModbusSequentialDataBlock(1, [0]*100),
    hr=ModbusSequentialDataBlock(1, [0]*100),
    ir=ModbusSequentialDataBlock(1, [0]*100),
)

context = ModbusServerContext(slaves=store, single=True)

print(">>> Modbus Simulator running on port 5020...")

StartTcpServer(
    context=context,
    address=("0.0.0.0", 5020)
)