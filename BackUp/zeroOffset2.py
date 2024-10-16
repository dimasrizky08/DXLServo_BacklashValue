import time
from dynamixel_sdk import *  # Menggunakan pustaka Dynamixel SDK

# Alamat control table untuk MX-106
ADDR_TORQUE_ENABLE = 512  # Alamat untuk menghidupkan torque
ADDR_GOAL_POSITION = 116   # Alamat goal position
ADDR_PRESENT_POSITION = 132 # Alamat present position

# Versi protokol
PROTOCOL_VERSION = 2.0  # MX-106 menggunakan Protokol 2.0

# Pengaturan default
DXL_ID = 1               # ID Dynamixel (sesuaikan dengan ID servo Anda)
BAUDRATE = 1000000       # Mengatur baudrate sesuai permintaan
DEVICENAME = '/dev/ttyUSB0'  # Sesuaikan dengan port USB di komputer Anda

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

# Batasan posisi
DXL_MINIMUM_POSITION_VALUE = 0      # Posisi minimum (disesuaikan)
DXL_MAXIMUM_POSITION_VALUE = 4095   # Posisi maksimum (disesuaikan)
DXL_MOVING_STATUS_THRESHOLD = 20     # Ambang batas status pergerakan

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
    # Menghidupkan torque
    packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
    print("Torque dihidupkan.")

    # Mengatur goal position ke posisi minimum untuk memulai
    goal_position = DXL_MINIMUM_POSITION_VALUE
    packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION, goal_position)
    print(f"Goal Position diatur ke: {goal_position}")

    # Loop untuk membaca posisi secara real-time setiap 0.1 detik
    while True:
        # Membaca present position
        present_position, dxl_comm_result, dxl_error = packetHandler.read2ByteTxRx(portHandler, DXL_ID, ADDR_PRESENT_POSITION)
        if dxl_comm_result != COMM_SUCCESS:
            print(f"Kesalahan dalam komunikasi (Present): {packetHandler.getTxRxResult(dxl_comm_result)}")
            break
        elif dxl_error != 0:
            print(f"Kesalahan di Dynamixel (Present): {packetHandler.getRxPacketError(dxl_error)}")
            break

        # Menampilkan posisi
        print(f"Present Position: {present_position}")

        # Menunggu 0.1 detik sebelum pembacaan berikutnya
        time.sleep(0.1)

finally:
    # Mematikan torque
    packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
    print("Torque dimatikan.")

    # Menutup port
    portHandler.closePort()
