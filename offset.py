import time
from dynamixel_sdk import *  

ADDR_TORQUE                 = 64   
ADDR_GOAL_POSITION          = 116   
ADDR_PRESENT_POSITION       = 132   

PROTOCOL_VERSION            = 2.0   

DXL_ID                      = 1              
BAUDRATE                    = 1000000        
DEVICENAME                  = '/dev/ttyUSB0' 

DXL_MINIMUM_POSITION_VALUE  = 10
DXL_MAXIMAL_POSITION_VALUE  = 4000
DXL_MOVING_STATUS_THRESHOLD = 20

inputDeg                    = 180
goal_position               = int(inputDeg / 360 * 4096)
minErr                      = 0
maxErr                      = 0

portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

if not portHandler.openPort():
    print("Gagal membuka port")
    exit()

if not portHandler.setBaudRate(BAUDRATE):
    print("Gagal mengatur baudrate")
    exit()

try:
    dxl_comm_result = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE, 1)
    packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION, goal_position)
    print(f"Bergerak ke {inputDeg} derajat\n...\n...")
    
    time.sleep(0.5)
    
    while True:
        goal_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION)
        present_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_PRESENT_POSITION)
        errorPos = present_position - goal_position
        
        if errorPos > maxErr:
            maxErr = errorPos
        
        elif errorPos < minErr:
            minErr = errorPos
        
        goalPosDeg      = goal_position / 4096 * 360
        presentPosDeg   = present_position / 4096 * 360
        minErrDeg       = minErr / 4096 * 360
        maxErrDeg       = maxErr / 4096 * 360
        
        print(f"Goal Position: {goalPosDeg :.2f} \t Present Position: {presentPosDeg :.2f} \t Degree Error Min: {minErrDeg :.2f} \t Degree Error Max: {maxErrDeg :.2f}")

        time.sleep(0.1)

finally:
    packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE, 0)
    print("Torque dimatikan.")
    portHandler.closePort()
