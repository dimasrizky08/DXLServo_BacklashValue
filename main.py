import sys
import time
import serial.tools.list_ports

from PySide6.QtWidgets import QLabel
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtGui import QPixmap, QTransform 
from PySide6.QtCore import Qt 
# from PySide6.QtWidgets import QFileDialog, QMessageBox, QDoubleSpinBox, QTextEdit, QRadioButton
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer
from dynamixel_sdk import *

ADDR_TORQUE = 64
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132

PROTOCOL_VERSION = 2.0
BAUDRATE = 1000000


packetHandler = PacketHandler(PROTOCOL_VERSION)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        ui_file = QFile("offset.ui")
        ui_file.open(QFile.ReadOnly)
        
        loader = QUiLoader()
        self.window = loader.load(ui_file, self)
        ui_file.close()

        self.servoID = self.window.findChild(QtWidgets.QSpinBox, "servoID")

        self.servoInputDeg = self.window.findChild(QtWidgets.QDoubleSpinBox, "servoInputDeg")

        self.connectionPort = self.window.findChild(QtWidgets.QComboBox, "connectionPort")
        self.connectButton = self.window.findChild(QtWidgets.QPushButton, "connectButton")
        self.disconnectButton = self.window.findChild(QtWidgets.QPushButton, "disconnectButton")
        self.exitButton = self.window.findChild(QtWidgets.QPushButton, "exitButton")

        self.minAngleText = self.window.findChild(QtWidgets.QDoubleSpinBox, "minAngleText")
        self.mainAngleText = self.window.findChild(QtWidgets.QDoubleSpinBox, "mainAngleText")
        self.maxAngleText = self.window.findChild(QtWidgets.QDoubleSpinBox, "maxAngleText")
        
        self.minValueText = self.window.findChild(QtWidgets.QDoubleSpinBox, "minValueText")
        self.mainValueText = self.window.findChild(QtWidgets.QDoubleSpinBox, "mainValueText")
        self.maxValueText = self.window.findChild(QtWidgets.QDoubleSpinBox, "maxValueText")
        
        self.minHornLabel = self.window.findChild(QtWidgets.QLabel, "minHorn")
        self.mainHornLabel = self.window.findChild(QtWidgets.QLabel, "mainHorn")
        self.maxHornLabel = self.window.findChild(QtWidgets.QLabel, "maxHorn")
        
        self.minHornAngle = 0  # Sudut rotasi untuk minHorn
        self.mainHornAngle = 0  # Sudut rotasi untuk mainHorn
        self.maxHornAngle = 0  # Sudut rotasi untuk maxHorn
        
        self.original_min_horn = self.minHornLabel.pixmap()  # Simpan gambar asli
        self.original_main_horn = self.mainHornLabel.pixmap()  # Simpan gambar asli
        self.original_max_horn = self.maxHornLabel.pixmap()


        self.refresh_ports()

        # Menghubungkan tombol Connect dengan fungsi
        self.connectButton.clicked.connect(self.connect_to_servo)
        self.disconnectButton.clicked.connect(self.disconnect)
        self.exitButton.clicked.connect(self.exitOffset)

        # Inisialisasi Timer untuk menggantikan while loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)  # Menghubungkan timeout dengan fungsi update_position

        # Tampilkan jendela
        self.window.show()

    def exitOffset(self):
        sys.exit()

    def disconnect(self):
        self.timer.stop()  # Berhenti memantau posisi saat disconnect
        self.connectButton.setText("Connect")
        servo_id = self.servoID.value()
        dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(self.portHandler, servo_id, ADDR_TORQUE, 0)
        if dxl_comm_result != COMM_SUCCESS:
            print(f"Kesalahan saat mematikan torque: {packetHandler.getTxRxResult(dxl_comm_result)}")
        # elif dxl_error != 0:
        #     print(f"Kesalahan dari servo: {packetHandler.getRxPacketError(dxl_error)}")
        
        print("Torque dimatikan.")
        self.portHandler.closePort()
        self.loop_active = False
    
    def refresh_ports(self):
        """Muat daftar port serial yang tersedia ke dalam QComboBox."""
        self.connectionPort.clear()  # Hapus semua item dari combobox

        # Dapatkan daftar port yang tersedia
        ports = serial.tools.list_ports.comports()

        # Tambahkan port yang tersedia ke combobox
        for port in ports:
            if "ttyUSB" in port.device:  # Hanya tambahkan port yang mengandung 'ttyUSB'
                self.connectionPort.addItem(port.device)

    def connect_to_servo(self):
        """Fungsi untuk menangani koneksi ke servo."""
        selected_port = self.connectionPort.currentText()  # Ambil port yang dipilih dari QComboBox
        self.connectButton.setText("Connected")
        if selected_port == "":
            print("Pilih port yang valid sebelum menghubungkan.")
            return

        # Menetapkan portHandler ke port yang dipilih dari combobox
        self.portHandler = PortHandler(selected_port)

        if not self.portHandler.openPort():
            print(f"Gagal membuka port: {selected_port}")
            return

        if not self.portHandler.setBaudRate(BAUDRATE):
            print(f"Gagal mengatur baudrate: {BAUDRATE}")
            return

        # Dapatkan nilai servo ID dan input derajat dari spinbox
        servo_id = self.servoID.value()
        input_deg = self.servoInputDeg.value()

        goal_position = int(int(input_deg) / 360 * 4096)

        dxl_comm_result = packetHandler.write1ByteTxRx(self.portHandler, servo_id, ADDR_TORQUE, 1)
        packetHandler.write4ByteTxRx(self.portHandler, servo_id, ADDR_GOAL_POSITION, goal_position)

        print(f"Bergerak ke {input_deg} derajat\n...\n...")
        time.sleep(0.5)

        self.maxErr = 0
        self.minErr = 0
        self.loop_active = True

        # Mulai timer dengan interval 100ms (0.1 detik)
        self.timer.start(100)

    def update_position(self):
        servo_id = self.servoID.value()
        goal_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(self.portHandler, servo_id, ADDR_GOAL_POSITION)
        present_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(self.portHandler, servo_id, ADDR_PRESENT_POSITION)

        errorPos = present_position - goal_position
        
        if errorPos > self.maxErr:
            self.maxErr = errorPos
        
        elif errorPos < self.minErr:
            self.minErr = errorPos

        goalPosDeg = goal_position / 4096 * 360
        presentPosDeg = present_position / 4096 * 360
        minErrDeg = self.minErr / 4096 * 360
        maxErrDeg = self.maxErr / 4096 * 360
        
        self.rotate_image(self.minHornLabel, minErrDeg)
        self.rotate_image(self.mainHornLabel, presentPosDeg)
        self.rotate_image(self.maxHornLabel, maxErrDeg)

        # Menampilkan nilai di text edits
        self.minAngleText.setValue(minErrDeg)
        self.mainAngleText.setValue(presentPosDeg)  
        self.maxAngleText.setValue(maxErrDeg)    
        
        self.minValueText.setValue(self.minErr)    
        self.mainValueText.setValue(present_position)   
        self.maxValueText.setValue(self.maxErr)
        
        
        print(f"{minErrDeg:.2f}\t {presentPosDeg:.2f}\t {maxErrDeg:.2f}")
        
    def rotate_image(self, label: QLabel, angle: float):
        """Memutar gambar pada QLabel berdasarkan sudut yang diberikan."""
        if label.pixmap() is None:
            return  # Pastikan ada gambar untuk diputar

        # Ambil gambar asli dari QLabel
        if label == self.minHornLabel:
            original_pixmap = self.original_min_horn
        elif label == self.mainHornLabel:
            original_pixmap = self.original_main_horn
        elif label == self.maxHornLabel:
            original_pixmap = self.original_max_horn
        else:
            return

        # Buat transformasi rotasi
        transform = QTransform().translate(original_pixmap.width() / 2, original_pixmap.height() / 2)
        transform.rotate(angle)
        transform.translate(-original_pixmap.width() / 2, -original_pixmap.height() / 2)

        # Terapkan transformasi untuk memutar gambar
        rotated_pixmap = original_pixmap.transformed(transform, Qt.SmoothTransformation)

        # Set QLabel untuk ukuran baru
        label.setPixmap(rotated_pixmap)
        
    def update_rotation(self):
        """Memperbarui rotasi gambar berdasarkan nilai error."""
        self.minHornAngle = self.minErrDeg  # Anggap minErrDeg diperoleh dari logika Anda
        self.mainHornAngle = self.presentPosDeg  # Anggap presentPosDeg diperoleh dari logika Anda
        self.maxHornAngle = self.maxErrDeg  # Anggap maxErrDeg diperoleh dari logika Anda

        # Panggil fungsi untuk memutar gambar
        self.rotate_image(self.minHornLabel, self.minHornAngle)
        self.rotate_image(self.mainHornLabel, self.mainHornAngle)
        self.rotate_image(self.maxHornLabel, self.maxHornAngle)

        
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()  # Membuat instance dari kelas MainWindow
    sys.exit(app.exec())
