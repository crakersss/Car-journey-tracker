import serial
import csv
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
import sys

# Configure serial port
SERIAL_PORT = 'COM3'
BAUD_RATE = 115200

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arduino GPS Logger")
        self.setFixedSize(300, 150)

        # Initialize variables
        self.ser = None
        self.csvfile = None
        self.csv_writer = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.read_serial)

        # Layout and buttons
        layout = QVBoxLayout()
        self.start_button = QPushButton("Start Recording")
        self.stop_button = QPushButton("Stop Recording")
        self.stop_button.setEnabled(False)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        # Set central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Connect buttons
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)

        # Select CSV file at startup
        self.csv_path = self.select_file()
        if not self.csv_path:
            print("No file selected. Exiting.")
            self.close()

    def select_file(self):
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("CSV files (*.csv)")
        file_dialog.setDefaultSuffix("csv")
        file_dialog.setWindowTitle("Choose where to save the CSV file")
        if file_dialog.exec_():
            return file_dialog.selectedFiles()[0]
        return None

    def start_recording(self):
        try:
            # Open serial connection
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"Connected to {SERIAL_PORT}")

            # Open CSV file
            self.csvfile = open(self.csv_path, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.csvfile)
            self.csv_writer.writerow(['timestamp', 'rpm', 'speed', 'lat', 'lon'])
            self.csvfile.flush()

            # Start reading serial data
            self.timer.start(100)  # Check every 100ms
            print(f"Logging to {self.csv_path}")

            # Update button states
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

        except serial.SerialException as e:
            print(f"Serial error: {e}")
            self.cleanup()

    def stop_recording(self):
        self.timer.stop()
        print(f"Stopped. Data saved to {self.csv_path}")
        self.cleanup()

    def read_serial(self):
        if self.ser and self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                # Skip initialization messages
                if line.startswith('timestamp') or line.startswith('NEO-6M'):
                    return
                # Parse data
                data = line.split(',')
                if len(data) == 5:  # Ensure correct number of fields
                    self.csv_writer.writerow(data)
                    self.csvfile.flush()
                    print(line)
            except ValueError:
                print(f"Skipping invalid line: {line}")

    def cleanup(self):
        if self.csvfile:
            self.csvfile.close()
            self.csvfile = None
        if self.ser:
            self.ser.close()
            self.ser = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        self.stop_recording()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()