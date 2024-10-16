import time
from dynamixel_sdk import *  # Menggunakan pustaka Dynamixel SDK

# Alamat control table untuk MX-106
ADDR_TORQUE_ENABLE          = 64   # Alamat untuk menghidupkan torque
ADDR_GOAL_POSITION          = 116   # Alamat goal position
ADDR_PRESENT_POSITION       = 132   # Alamat present position

# Versi protokol
PROTOCOL_VERSION            = 2.0   # MX-106 menggunakan Protokol 2.0

# Pengaturan default
DXL_ID                      = 1              # ID Dynamixel (sesuaikan dengan ID servo Anda)
BAUDRATE                    = 1000000        # Mengatur baudrate sesuai permintaan
DEVICENAME                  = '/dev/ttyUSB0' # Sesuaikan dengan port USB di komputer Anda (Linux)

TORQUE_ENABLE               = 1
TORQUE_DISABLE              = 0
DXL_MINIMUM_POSITION_VALUE  = 10
DXL_MAXIMAL_POSITION_VALUE  = 4000
DXL_MOVING_STATUS_THRESHOLD = 20 

# Inisialisasi PortHandler
portHandler = PortHandler(DEVICENAME)

# Inisialisasi PacketHandler
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
    # Menghidupkan torque
    dxl_comm_result = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
    if dxl_comm_result != COMM_SUCCESS:
        print(f"Kesalahan dalam komunikasi saat menghidupkan torque: {packetHandler.getTxRxResult(dxl_comm_result)}")
    else:
        print("Torque dihidupkan.")

    # Mengatur goal position ke 0
    goal_position = 2048
    packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION, goal_position)
    print(f"Goal Position diatur ke: {goal_position}")

    # Tunggu hingga servo mencapai goal position
    while True:
        present_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_PRESENT_POSITION)
        if dxl_comm_result != COMM_SUCCESS:
            print(f"Kesalahan dalam komunikasi (Present): {packetHandler.getTxRxResult(dxl_comm_result)}")
            break
        elif dxl_error != 0:
            print(f"Kesalahan di Dynamixel (Present): {packetHandler.getRxPacketError(dxl_error)}")
            break
        
        print(f"[INFO] Present Position: {present_position}")

        # Cek apakah servo sudah mencapai goal position
        if abs(goal_position - present_position) < DXL_MOVING_STATUS_THRESHOLD:
            print("Servo sudah mencapai goal position.")
            break

        # Tunggu sejenak sebelum pengecekan berikutnya
        time.sleep(0.1)

    # Loop untuk membaca posisi secara real-time setiap 0.1 detik
    while True:
        # Membaca goal position
        goal_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION)
        # if dxl_comm_result != COMM_SUCCESS:
        #     print(f"Kesalahan dalam komunikasi (Goal): {packetHandler.getTxRxResult(dxl_comm_result)}")
        # elif dxl_error != 0:
        #     print(f"Kesalahan di Dynamixel (Goal): {packetHandler.getRxPacketError(dxl_error)}")

        # Membaca present position
        present_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_PRESENT_POSITION)
        # if dxl_comm_result != COMM_SUCCESS:
        #     print(f"Kesalahan dalam komunikasi (Present): {packetHandler.getTxRxResult(dxl_comm_result)}")
        # elif dxl_error != 0:
        #     print(f"Kesalahan di Dynamixel (Present): {packetHandler.getRxPacketError(dxl_error)}")

        # Menampilkan posisi
        print(f"Goal Position: {goal_position}, Present Position: {present_position}")

        # Tunggu 0.1 detik sebelum pembacaan berikutnya
        time.sleep(0.1)

finally:
    # Mematikan torque sebelum menutup port
    packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
    print("Torque dimatikan.")
    
    # Menutup port
    portHandler.closePort()
