import sys
import obd  # OBD2 library
import warnings
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QLineEdit, QStackedWidget  # GUI components
from PyQt5.QtCore import QTimer, Qt, QThread, QObject, pyqtSignal  # Timer, alignment, and threading utilities
from qroundprogressbar import QRoundProgressBar  # Custom gauges
import time  # For runtime tracking
import serial.tools.list_ports  # For detecting COM ports

# Suppress DeprecationWarning from sip to avoid cluttering output
warnings.filterwarnings("ignore", category=DeprecationWarning, message="sipPyTypeDict.* is deprecated")

# Constants for gauges
MIN_RPM = 3000  # Minimum allowable RPM
MAX_RPM_LIMIT = 12000  # Maximum allowable RPM
MIN_SPEED = 100  # Minimum allowable speed
MAX_SPEED_LIMIT = 400  # Maximum allowable speed
DEFAULT_MAX_RPM = 8000  # Default max RPM
DEFAULT_MAX_SPEED = 240  # Default max speed
GAUGE_SIZE_LARGE = (260, 260)  # Size for gauges
GAUGE_SIZE_SMALL = (120, 120)  # Size for gauges
DATA_PEN_WIDTH_LARGE = 10  # Large guage thickness 
DATA_PEN_WIDTH_SMALL = 6  # Small gauge thickness
RPM_UPDATE_INTERVAL = 50  # Update interval for RPM - to prioritise RPM
OTHER_UPDATE_INTERVAL = 1000  # Update interval for other data
THROTTLE_MAX = 100  # Maximum throttle position
TEMP_MAX = 150  # Maximum coolant temperature
LOAD_MAX = 100  # Maximum engine load
BOOST_MAX = 3  # Maximum boost pressure

class OBDConnectionWorker(QObject):
    """Worker to handle OBD-II connection in a separate thread"""
    connection_result = pyqtSignal(object)  # Signal to send connection result back to main thread

    def run(self):
        """Attempt to connect to OBD-II adapter"""
        print("Status: Scanning for OBD-II ports:", obd.scan_serial())
        ports = [port.device for port in serial.tools.list_ports.comports()]
        print("Available COM ports:", ports)

        connection = None
        for attempt in range(3):
            for port in ['COM4'] + ports:
                try:
                    connection = obd.OBD(portstr=port, timeout=5)
                    connection.query(obd.commands.ELM_VERSION)
                    if connection.is_connected():
                        print(f"Connected to {port} on attempt {attempt + 1}")
                        rpm_response = connection.query(obd.commands.RPM)
                        if rpm_response and not rpm_response.is_null() and rpm_response.value.magnitude > 0:
                            self.connection_result.emit(connection)
                            return
                        print("Ignition off or no RPM response—connection may fail.")
                        self.connection_result.emit(connection)
                        return
                except Exception as e:
                    print(f"Failed to connect to {port}: {e}")
                    connection = None
            time.sleep(1)
        print("All connection attempts failed.")
        self.connection_result.emit(None)

class OBDGui(QWidget):
    def __init__(self):
        """Initialize the OBD-II GUI app."""
        super().__init__()
        self.connection = None  # OBD-II connection object
        self.start_time = time.time()  # Track start time for runtime
        self.current_rpm = 0  # Current engine RPM
        self.current_speed = 0  # Current vehicle speed
        self.current_throttle = 0  # Current throttle position
        self.current_temp = 0  # Current coolant temperature
        self.current_load = 0  # Current engine load
        self.current_boost = 0  # Current boost pressure

        # Set up widget for switching between setup and main pages
        self.stacked_widget = QStackedWidget()
        self.setup_page = QWidget()
        self.main_page = QWidget()
        self._init_setup_page()
        self._init_main_page()
        self.stacked_widget.addWidget(self.setup_page)
        self.stacked_widget.addWidget(self.main_page)
        self.stacked_widget.setCurrentIndex(0)

        # Apply layout to main window
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)
        self.show()

    def _init_setup_page(self):
        """Set up the config page for gauge settings."""
        self.setWindowTitle("OBD-II Monitor Setup")
        self.setGeometry(100, 100, 400, 300)  # Window size and position
        setup_layout = QVBoxLayout()

        # Title for setup page
        setup_label = QLabel("Configure Gauges")
        setup_label.setAlignment(Qt.AlignCenter)
        setup_layout.addWidget(setup_label)

        # Instructions for user input
        instructions = f"Enter your car's maximum RPM ({MIN_RPM}–{MAX_RPM_LIMIT}) and speed ({MIN_SPEED}–{MAX_SPEED_LIMIT} km/h)."
        instructions_label = QLabel(instructions)
        instructions_label.setAlignment(Qt.AlignCenter)
        instructions_label.setStyleSheet("font-weight: bold;")
        instructions_label.setWordWrap(True)
        setup_layout.addWidget(instructions_label)

        # Error message for invalid inputs
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        setup_layout.addWidget(self.error_label)

        # Input for max RPM
        rpm_layout = QHBoxLayout()
        rpm_label = QLabel("Max RPM:")
        self.rpm_input = QLineEdit(str(DEFAULT_MAX_RPM))
        self.rpm_input.setFixedWidth(100)
        rpm_layout.addWidget(rpm_label)
        rpm_layout.addWidget(self.rpm_input)
        setup_layout.addLayout(rpm_layout)

        # Input for max speed
        speed_layout = QHBoxLayout()
        speed_label = QLabel("Max Speed (km/h):")
        self.speed_input = QLineEdit(str(DEFAULT_MAX_SPEED))
        self.speed_input.setFixedWidth(100)
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_input)
        setup_layout.addLayout(speed_layout)

        # Button to start monitoring
        self.start_button = QPushButton("Start Monitoring")  # Store reference to the button
        self.start_button.clicked.connect(self.start_monitoring)
        setup_layout.addWidget(self.start_button, alignment=Qt.AlignCenter)

        self.setup_page.setLayout(setup_layout)

    def _init_main_page(self):
        """Set up the main page with gauges and controls."""
        main_layout = QVBoxLayout()
        self.status_label = QLabel("Initializing...")  # Status message
        main_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

        # Add RPM and speed gauges
        top_gauge_layout = QHBoxLayout()
        self._add_rpm_gauge(top_gauge_layout)
        self._add_speed_gauge(top_gauge_layout)
        main_layout.addLayout(top_gauge_layout)

        # Add load and boost gauges
        mid_gauge_layout = QHBoxLayout()
        self._add_load_gauge(mid_gauge_layout)
        self._add_boost_gauge(mid_gauge_layout)
        main_layout.addLayout(mid_gauge_layout)

        # Add throttle and temp bars
        self._add_throttle_bar(main_layout)
        self._add_temp_bar(main_layout)
        self._add_info_labels(main_layout)

        # Setup return button
        self.reconfigure_button = QPushButton("Reconfigure")
        self.reconfigure_button.clicked.connect(self.reconfigure)
        main_layout.addWidget(self.reconfigure_button)

        # Ext button
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        main_layout.addWidget(self.exit_button)

        # Timers for updating data
        self.rpm_timer = QTimer(self)
        self.rpm_timer.timeout.connect(self.fast_rpm_update)
        self.other_timer = QTimer(self)
        self.other_timer.timeout.connect(self.update_others)

        self.main_page.setLayout(main_layout)

    def _add_rpm_gauge(self, layout):
        """Add RPM gauge to specified layout"""
        rpm_container = QVBoxLayout()
        self.rpm_title = QLabel("Engine RPM")
        rpm_container.addWidget(self.rpm_title, alignment=Qt.AlignCenter)
        self.rpm_gauge = QRoundProgressBar()
        self.rpm_gauge.setMinimum(0)
        self.rpm_gauge.setMaximum(DEFAULT_MAX_RPM)
        self.rpm_gauge.setValue(0)
        self.rpm_gauge.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.rpm_gauge.setFixedSize(*GAUGE_SIZE_LARGE)
        self.rpm_gauge.setDataPenWidth(DATA_PEN_WIDTH_LARGE)
        self.rpm_gauge.setFormat("%v RPM")
        rpm_container.addWidget(self.rpm_gauge, alignment=Qt.AlignCenter)
        layout.addLayout(rpm_container)

    def _add_speed_gauge(self, layout):
        """Add speed gauge to layout"""
        speed_container = QVBoxLayout()
        self.speed_title = QLabel("Vehicle Speed")
        speed_container.addWidget(self.speed_title, alignment=Qt.AlignCenter)
        self.speed_gauge = QRoundProgressBar()
        self.speed_gauge.setMinimum(0)
        self.speed_gauge.setMaximum(DEFAULT_MAX_SPEED)
        self.speed_gauge.setValue(0)
        self.speed_gauge.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.speed_gauge.setFixedSize(*GAUGE_SIZE_LARGE)
        self.speed_gauge.setDataPenWidth(DATA_PEN_WIDTH_LARGE)
        self.speed_gauge.setFormat("%v km/h")
        speed_container.addWidget(self.speed_gauge, alignment=Qt.AlignCenter)
        layout.addLayout(speed_container)

    def _add_load_gauge(self, layout):
        """Add engine load gauge to layout"""
        self.load_title = QLabel("Engine Load")
        layout.addWidget(self.load_title, alignment=Qt.AlignCenter)
        self.load_gauge = QRoundProgressBar()
        self.load_gauge.setMinimum(0)
        self.load_gauge.setMaximum(LOAD_MAX)
        self.load_gauge.setValue(0)
        self.load_gauge.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.load_gauge.setFixedSize(*GAUGE_SIZE_SMALL)
        self.load_gauge.setDataPenWidth(DATA_PEN_WIDTH_SMALL)
        self.load_gauge.setFormat("%v %")
        layout.addWidget(self.load_gauge, alignment=Qt.AlignCenter)

    def _add_boost_gauge(self, layout):
        """Add boost pressure gauge to layout"""
        self.boost_title = QLabel("Boost Pressure")
        layout.addWidget(self.boost_title, alignment=Qt.AlignCenter)
        self.boost_gauge = QRoundProgressBar()
        self.boost_gauge.setMinimum(0)
        self.boost_gauge.setMaximum(BOOST_MAX)
        self.boost_gauge.setValue(1)  # Default to atmospheric pressure
        self.boost_gauge.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.boost_gauge.setFixedSize(*GAUGE_SIZE_SMALL)
        self.boost_gauge.setDataPenWidth(DATA_PEN_WIDTH_SMALL)
        self.boost_gauge.setFormat("%.1f bar")
        layout.addWidget(self.boost_gauge, alignment=Qt.AlignCenter)

    def _add_throttle_bar(self, layout):
        """Add throttle position bar to layout"""
        self.throttle_title = QLabel("Throttle Position")
        layout.addWidget(self.throttle_title, alignment=Qt.AlignCenter)
        self.throttle_bar = QProgressBar()
        self.throttle_bar.setMinimum(0)
        self.throttle_bar.setMaximum(THROTTLE_MAX)
        self.throttle_bar.setValue(0)
        self.throttle_bar.setOrientation(Qt.Horizontal)
        self.throttle_bar.setFixedSize(300, 30)
        self.throttle_bar.setFormat("%v %")
        self.throttle_bar.setTextVisible(True)
        self.throttle_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                background-color: #E0E0E0;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #33CC33;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.throttle_bar, alignment=Qt.AlignCenter)

    def _add_temp_bar(self, layout):
        """Add coolant temp bar to layout"""
        self.temp_title = QLabel("Coolant Temperature")
        layout.addWidget(self.temp_title, alignment=Qt.AlignCenter)
        self.temp_bar = QProgressBar()
        self.temp_bar.setMinimum(0)
        self.temp_bar.setMaximum(TEMP_MAX)
        self.temp_bar.setValue(0)
        self.temp_bar.setOrientation(Qt.Horizontal)
        self.temp_bar.setFixedSize(300, 30)
        self.temp_bar.setFormat("%v °C")
        self.temp_bar.setTextVisible(True)
        self.temp_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                background-color: #E0E0E0;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #FF3333;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.temp_bar, alignment=Qt.AlignCenter)

    def _add_info_labels(self, layout):
        """Add labels for displaying current values"""
        self.rpm_label = QLabel("RPM: 0")
        layout.addWidget(self.rpm_label, alignment=Qt.AlignCenter)
        self.speed_label = QLabel("Speed: 0 km/h")
        layout.addWidget(self.speed_label, alignment=Qt.AlignCenter)
        self.throttle_label = QLabel("Throttle: 0 %")
        layout.addWidget(self.throttle_label, alignment=Qt.AlignCenter)
        self.temp_label = QLabel("Temp: 0 °C")
        layout.addWidget(self.temp_label, alignment=Qt.AlignCenter)
        self.runtime_label = QLabel("Run Time: 00:00")
        layout.addWidget(self.runtime_label, alignment=Qt.AlignCenter)

    def start_monitoring(self):
        """Validate user input and start monitoring data"""
        try:
            rpm = int(self.rpm_input.text())
            speed = int(self.speed_input.text())
            if not (MIN_RPM <= rpm <= MAX_RPM_LIMIT):
                self.error_label.setText(f"Max RPM out of range ({MIN_RPM}–{MAX_RPM_LIMIT}).")
                return
            if not (MIN_SPEED <= speed <= MAX_SPEED_LIMIT):
                self.error_label.setText(f"Max Speed out of range ({MIN_SPEED}–{MAX_SPEED_LIMIT} km/h).")
                return
            self.max_rpm = rpm
            self.max_speed = speed
            self.error_label.setText("")
        except ValueError:
            self.error_label.setText("Invalid input: Please enter positive integers")
            return

        self.rpm_gauge.setMaximum(self.max_rpm)
        self.speed_gauge.setMaximum(self.max_speed)
        
        # Start the connection in a separate thread
        self.status_label.setText("Connecting to OBD-II adapter...")
        self.start_button.setEnabled(False)  # Disable button while connecting
        self.connection_thread = QThread()
        self.connection_worker = OBDConnectionWorker()
        self.connection_worker.moveToThread(self.connection_thread)
        self.connection_thread.started.connect(self.connection_worker.run)
        self.connection_worker.connection_result.connect(self.on_connection_result)
        self.connection_thread.start()

    def on_connection_result(self, connection):
        """Handle the result of the OBD-II connection attempt"""
        self.connection = connection
        self.start_button.setEnabled(True)  # Re-enable the start button
        
        if self.connection and self.connection.is_connected():
            self.status_label.setText("✅ OBD-II adapter connected.")
            self.rpm_timer.start(RPM_UPDATE_INTERVAL)
            self.other_timer.start(OTHER_UPDATE_INTERVAL)
            print("Status: OBD-II adapter connected on", self.connection.port_name())
            print("Supported commands:", [cmd.name for cmd in self.connection.supported_commands])
        else:
            self.status_label.setText("❌ No OBD-II adapter detected. Check ignition and COM port.")
            print("Status: Failed to connect to OBD-II adapter.")

        self.stacked_widget.setCurrentIndex(1)
        self.setWindowTitle("OBD-II Monitor")
        self.setGeometry(100, 100, 800, 650)

        # Clean up the thread
        self.connection_thread.quit()
        self.connection_thread.wait()

    def reconfigure(self):
        """Stop updates and return to setup page"""
        if self.connection and self.connection.is_connected():
            self.rpm_timer.stop()
            self.other_timer.stop()
        self.rpm_input.setText(str(self.max_rpm))
        self.speed_input.setText(str(self.max_speed))
        self.stacked_widget.setCurrentIndex(0)
        self.setWindowTitle("OBD-II Monitor Setup")
        self.setGeometry(100, 100, 400, 300)

    def connect_obd(self):
        """Attempt to connect to the OBD-II adapter"""
        # This method is now handled by OBDConnectionWorker
        pass

    def update_display(self):
        """Update GUI with latest OBD-II data"""
        if not self.connection or not self.connection.is_connected():
            return
        self.rpm_gauge.setValue(int(self.current_rpm))
        self.rpm_label.setText(f"RPM: {int(self.current_rpm)}")
        self.speed_gauge.setValue(int(self.current_speed))
        self.speed_label.setText(f"Speed: {int(self.current_speed)} km/h")
        self.throttle_bar.setValue(int(self.current_throttle))
        self.throttle_label.setText(f"Throttle: {int(self.current_throttle)} %")
        self.temp_bar.setValue(int(self.current_temp))
        self.temp_label.setText(f"Temp: {int(self.current_temp)} °C")
        self.load_gauge.setValue(int(self.current_load))
        self.boost_gauge.setValue(self.current_boost)
        runtime_secs = int(time.time() - self.start_time)
        mins, secs = divmod(runtime_secs, 60)
        self.runtime_label.setText(f"Run Time: {mins:02d}:{secs:02d}")

    def fast_rpm_update(self):
        """Update RPM data at a faster interval"""
        if self.connection and self.connection.is_connected():
            response = self.connection.query(obd.commands.RPM)
            if response and not response.is_null():
                self.current_rpm = int(response.value.magnitude)
                self.update_display()

    def update_others(self):
        """Update non-RPM data at a slower interval"""
        if self.connection and self.connection.is_connected():
            responses = {
                "speed": self.connection.query(obd.commands.SPEED),
                "throttle": self.connection.query(obd.commands.THROTTLE_POS),
                "load": self.connection.query(obd.commands.ENGINE_LOAD),
                "temp": self.connection.query(obd.commands.COOLANT_TEMP)
            }
            if responses["speed"] and not responses["speed"].is_null():
                self.current_speed = int(responses["speed"].value.magnitude)
            if responses["throttle"] and not responses["throttle"].is_null():
                self.current_throttle = int(responses["throttle"].value.magnitude)
            if responses["load"] and not responses["load"].is_null():
                self.current_load = int(responses["load"].value.magnitude)
            if responses["temp"] and not responses["temp"].is_null():
                self.current_temp = int(responses["temp"].value.magnitude)
            self.current_boost = 1 + min(1.5, max(-0.5, (self.current_load / 100) * (self.current_rpm / self.max_rpm) * 1.5))
            self.update_display()

    def closeEvent(self, event):
        """Close OBD-II connection"""
        if self.connection and self.connection.is_connected():
            print("Closing OBD connection...")
            self.connection.close()
        event.accept()

if __name__ == "__main__":
    """Start the application and handle exceptions"""
    app = QApplication(sys.argv)
    try:
        gui = OBDGui()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")