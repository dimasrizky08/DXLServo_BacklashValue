import time
from dynamixel_sdk import *  

# Alamat control table untuk DYNAMIXEL MX-106
ADDR_TORQUE_ENABLE          = 64   
ADDR_GOAL_POSITION          = 116   
ADDR_PRESENT_POSITION       = 132   

PROTOCOL_VERSION            = 2.0   

# Pengaturan default
BAUDRATE                    = 1000000        
DEVICENAME                  = '/dev/ttyUSB0' 

TORQUE_ENABLE               = 1
TORQUE_DISABLE              = 0
DXL_MINIMUM_POSITION_VALUE  = 10
DXL_MAXIMAL_POSITION_VALUE  = 4000
DXL_MOVING_STATUS_THRESHOLD = 20

# Input derajat dan konversi ke posisi goal
inputDeg                    = 180
goal_position               = int(inputDeg / 360 * 4096)

# Inisialisasi PortHandler dan PacketHandler
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

# Membuka port
if not portHandler.openPort():
    print("Gagal membuka port")
    exit()

# Mengatur baudrate port
if not portHandler.setBaudRate(BAUDRATE):
    print("Gagal mengatur baudrate")
    exit()

try:
    # Menghidupkan torque untuk semua servo dari ID 1 sampai 20
    detected_servos = []  # List untuk menyimpan servo yang terdeteksi

    for DXL_ID in range(1, 21):
        dxl_comm_result = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
        if dxl_comm_result == COMM_SUCCESS:
            detected_servos.append(DXL_ID)
            print(f"Torque dihidupkan pada ID {DXL_ID}.")
        else:
            print(f"Gagal menghidupkan torque pada ID {DXL_ID}: {packetHandler.getTxRxResult(dxl_comm_result)}")

    # Menulis goal position untuk servo yang terdeteksi
    for DXL_ID in detected_servos:
        packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION, goal_position)

    while True:
        # Membaca posisi untuk semua servo yang terdeteksi
        for DXL_ID in detected_servos:
            goal_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION)
            present_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_PRESENT_POSITION)
            
            # Cek hasil komunikasi
            if dxl_comm_result != COMM_SUCCESS:
                print(f"Kesalahan komunikasi pada ID {DXL_ID} (Goal): {packetHandler.getTxRxResult(dxl_comm_result)}")
                continue
            
            if dxl_error != 0:
                print(f"Kesalahan di Dynamixel pada ID {DXL_ID} (Goal): {packetHandler.getRxPacketError(dxl_error)}")
                continue

            # Menghitung error posisi
            errorPos = present_position - goal_position
            
            # Konversi posisi dari PWM ke derajat
            PWMtoDeg = 1 / 4096 * 360
            goalPosDeg      = goal_position * PWMtoDeg
            presentPosDeg   = present_position * PWMtoDeg
            
            print(f"ID {DXL_ID} - Goal Position: {goalPosDeg:.2f} \t Present Position: {presentPosDeg:.2f} \t Error: {errorPos:.2f}")

        time.sleep(0.1)

finally:
    # Mematikan torque untuk semua servo yang terdeteksi
    for DXL_ID in detected_servos:
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
        print(f"Torque dimatikan pada ID {DXL_ID}.")

    portHandler.closePort()
