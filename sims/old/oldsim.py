import sys
import warnings
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QSlider, QLineEdit, QStackedWidget
from PyQt5.QtCore import QTimer, Qt
from qroundprogressbar import QRoundProgressBar
import time

# Suppress the specific DeprecationWarning from sip
warnings.filterwarnings("ignore", category=DeprecationWarning, message="sipPyTypeDict.* is deprecated")

class OBDGui(QWidget):
    def __init__(self):
        super().__init__()
        self.min_rpm = 3000
        self.max_rpm_limit = 12000
        self.min_speed = 100
        self.max_speed_limit = 400

        self.max_rpm = 8000
        self.max_speed = 240
        self.current_rpm = 0
        self.current_speed = 0
        self.current_temp = 90
        self.current_throttle = 0
        self.current_load = 0
        self.current_boost = 0
        self.current_gear = "N"
        self.start_time = time.time()
        self.sim_throttle = 0
        self.sim_gear = 0
        self.throttle_pressed = False
        self.clutch_pressed = False
        self.turbo_boost = 0
        self.engine_stalled = False

        self.stacked_widget = QStackedWidget()
        self.setup_page = QWidget()
        self.main_page = QWidget()
        self.init_setup_page()
        self.init_main_page()
        self.stacked_widget.addWidget(self.setup_page)
        self.stacked_widget.addWidget(self.main_page)
        self.stacked_widget.setCurrentIndex(0)

        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        self.update_status()
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.fast_update)
        self.show()

    def init_setup_page(self):
        self.setWindowTitle("OBD-II Simulator Setup")
        self.setGeometry(100, 100, 400, 300)

        setup_layout = QVBoxLayout()

        setup_label = QLabel("Configure Gauges")
        setup_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        setup_layout.addWidget(setup_label)

        instructions_label = QLabel(f"Enter your car's maximum RPM ({self.min_rpm}–{self.max_rpm_limit}) and speed ({self.min_speed}–{self.max_speed_limit} km/h) in the fields below.")
        instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions_label.setStyleSheet("font-weight: bold;")
        instructions_label.setWordWrap(True)
        setup_layout.addWidget(instructions_label)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        setup_layout.addWidget(self.error_label)

        rpm_layout = QHBoxLayout()
        rpm_label = QLabel("Max RPM:")
        self.rpm_input = QLineEdit("8000")
        self.rpm_input.setFixedWidth(100)
        rpm_layout.addWidget(rpm_label)
        rpm_layout.addWidget(self.rpm_input)
        setup_layout.addLayout(rpm_layout)

        speed_layout = QHBoxLayout()
        speed_label = QLabel("Max Speed (km/h):")
        self.speed_input = QLineEdit("240")
        self.speed_input.setFixedWidth(100)
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_input)
        setup_layout.addLayout(speed_layout)

        start_button = QPushButton("Start Monitoring")
        start_button.clicked.connect(self.start_monitoring)
        setup_layout.addWidget(start_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setup_page.setLayout(setup_layout)

    def start_monitoring(self):
        try:
            rpm = int(self.rpm_input.text())
            speed = int(self.speed_input.text())

            if rpm < self.min_rpm or rpm > self.max_rpm_limit:
                self.error_label.setText(f"Max RPM out of range ({self.min_rpm}–{self.max_rpm_limit}). Please retry.")
                return
            if speed < self.min_speed or speed > self.max_speed_limit:
                self.error_label.setText(f"Max Speed out of range ({self.min_speed}–{self.max_speed_limit} km/h). Please retry.")
                return

            self.max_rpm = rpm
            self.max_speed = speed
            self.error_label.setText("")
        except ValueError as e:
            self.error_label.setText("Invalid input: Please enter positive integers")
            return

        self.rpm_gauge.setMaximum(self.max_rpm)
        self.speed_gauge.setMaximum(self.max_speed)

        self.update_timer.start(50)
        self.stacked_widget.setCurrentIndex(1)
        self.setWindowTitle("OBD-II Simulator")
        self.setGeometry(100, 100, 800, 700)

    def reconfigure(self):
        self.update_timer.stop()
        self.rpm_input.setText(str(self.max_rpm))
        self.speed_input.setText(str(self.max_speed))
        self.stacked_widget.setCurrentIndex(0)
        self.setWindowTitle("OBD-II Simulator Setup")
        self.setGeometry(100, 100, 400, 300)

    def update_status(self):
        if self.engine_stalled:
            self.status_label.setText("💀 Engine Stalled! Press R to Restart (Hold Enter: Throttle, Space: Clutch, W: Up, S: Down)")
        else:
            self.status_label.setText("🚗 Simulation Mode ON (Hold Enter: Throttle, Space: Clutch, W: Gear Up, S: Gear Down)")

    def init_main_page(self):
        main_layout = QVBoxLayout()

        self.status_label = QLabel("Initializing...")
        main_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        top_gauge_layout = QHBoxLayout()

        rpm_container = QVBoxLayout()
        self.rpm_title = QLabel("Engine RPM")
        rpm_container.addWidget(self.rpm_title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.rpm_gauge = QRoundProgressBar()
        self.rpm_gauge.setMinimum(0)
        self.rpm_gauge.setMaximum(self.max_rpm)
        self.rpm_gauge.setValue(int(self.current_rpm))
        self.rpm_gauge.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.rpm_gauge.setFixedSize(260, 260)  # Increased size to prevent clipping
        self.rpm_gauge.setDataPenWidth(10)  # Reduced thickness to prevent clipping
        self.rpm_gauge.setFormat("%v RPM")
        rpm_container.addWidget(self.rpm_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        top_gauge_layout.addLayout(rpm_container)

        speed_container = QVBoxLayout()
        self.speed_title = QLabel("Vehicle Speed")
        speed_container.addWidget(self.speed_title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.speed_gauge = QRoundProgressBar()
        self.speed_gauge.setMinimum(0)
        self.speed_gauge.setMaximum(self.max_speed)
        self.speed_gauge.setValue(int(self.current_speed))
        self.speed_gauge.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.speed_gauge.setFixedSize(260, 260)  # Increased size to prevent clipping
        self.speed_gauge.setDataPenWidth(10)  # Reduced thickness to prevent clipping
        self.speed_gauge.setFormat("%v km/h")
        speed_container.addWidget(self.speed_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        top_gauge_layout.addLayout(speed_container)
        main_layout.addLayout(top_gauge_layout)

        mid_gauge_layout = QHBoxLayout()

        self.load_title = QLabel("Engine Load")
        mid_gauge_layout.addWidget(self.load_title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.load_gauge = QRoundProgressBar()
        self.load_gauge.setMinimum(0)
        self.load_gauge.setMaximum(100)
        self.load_gauge.setValue(int(self.current_load))
        self.load_gauge.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.load_gauge.setFixedSize(120, 120)
        self.load_gauge.setDataPenWidth(6)  # Reduced thickness for consistency
        self.load_gauge.setFormat("%v %")
        mid_gauge_layout.addWidget(self.load_gauge, alignment=Qt.AlignmentFlag.AlignCenter)

        self.boost_title = QLabel("Boost Pressure")
        mid_gauge_layout.addWidget(self.boost_title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.boost_gauge = QRoundProgressBar()
        self.boost_gauge.setMinimum(0)
        self.boost_gauge.setMaximum(3)
        self.boost_gauge.setValue(1)
        self.boost_gauge.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.boost_gauge.setFixedSize(120, 120)
        self.boost_gauge.setDataPenWidth(6)  # Reduced thickness for consistency
        self.boost_gauge.setFormat("%.1f bar")
        mid_gauge_layout.addWidget(self.boost_gauge, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addLayout(mid_gauge_layout)

        self.throttle_title = QLabel("Throttle Position")
        main_layout.addWidget(self.throttle_title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.throttle_bar = QProgressBar()
        self.throttle_bar.setMinimum(0)
        self.throttle_bar.setMaximum(100)
        self.throttle_bar.setValue(int(self.current_throttle))
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
        main_layout.addWidget(self.throttle_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.temp_title = QLabel("Coolant Temperature")
        main_layout.addWidget(self.temp_title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.temp_bar = QProgressBar()
        self.temp_bar.setMinimum(0)
        self.temp_bar.setMaximum(150)
        self.temp_bar.setValue(int(self.current_temp))
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
                background-color: "FF3333";
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.temp_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.rpm_label = QLabel(f"RPM: {self.current_rpm}")
        main_layout.addWidget(self.rpm_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.speed_label = QLabel(f"Speed: {self.current_speed} km/h")
        main_layout.addWidget(self.speed_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.throttle_label = QLabel(f"Throttle: {self.current_throttle} %")
        main_layout.addWidget(self.throttle_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.temp_label = QLabel(f"Temp: {self.current_temp} °C")
        main_layout.addWidget(self.temp_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.gear_label = QLabel(f"Gear: {self.current_gear}")
        main_layout.addWidget(self.gear_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.runtime_label = QLabel("Run Time: 00:00")
        main_layout.addWidget(self.runtime_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.sim_controls_layout = QHBoxLayout()
        self.throttle_slider = QSlider(Qt.Horizontal)
        self.throttle_slider.setMinimum(0)
        self.throttle_slider.setMaximum(100)
        self.throttle_slider.setValue(0)
        self.throttle_slider.valueChanged.connect(self.update_sim_throttle)
        self.sim_controls_layout.addWidget(QLabel("Sim Throttle:"))
        self.sim_controls_layout.addWidget(self.throttle_slider)

        self.gear_up_button = QPushButton("Gear Up (W)")
        self.gear_up_button.clicked.connect(self.gear_up)
        self.sim_controls_layout.addWidget(self.gear_up_button)

        self.gear_down_button = QPushButton("Gear Down (S)")
        self.gear_down_button.clicked.connect(self.gear_down)
        self.sim_controls_layout.addWidget(self.gear_down_button)

        main_layout.addLayout(self.sim_controls_layout)

        self.reconfigure_button = QPushButton("Reconfigure")
        self.reconfigure_button.clicked.connect(self.reconfigure)
        main_layout.addWidget(self.reconfigure_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        main_layout.addWidget(self.exit_button)

        self.main_page.setLayout(main_layout)

    def update_sim_throttle(self, value):
        self.sim_throttle = value
        self.throttle_slider.setValue(int(value))

    def gear_up(self):
        if self.clutch_pressed and self.sim_gear < 5:
            self.sim_gear += 1
            self.current_gear = "N" if self.sim_gear == 0 else str(self.sim_gear)

    def gear_down(self):
        if self.clutch_pressed and self.sim_gear > 0:
            self.sim_gear -= 1
            self.current_gear = "N" if self.sim_gear == 0 else str(self.sim_gear)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not self.throttle_pressed and not self.engine_stalled:
            self.throttle_pressed = True
        elif event.key() == Qt.Key_Space and not self.clutch_pressed:
            self.clutch_pressed = True
        elif event.key() == Qt.Key_W:
            self.gear_up()
        elif event.key() == Qt.Key_S:
            self.gear_down()
        elif event.key() == Qt.Key_R and self.engine_stalled:
            self.engine_stalled = False
            self.current_rpm = 750
            self.update_status()
        event.accept()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.throttle_pressed = False
        elif event.key() == Qt.Key_Space:
            self.clutch_pressed = False
        event.accept()

    def update_display(self):
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
        self.gear_label.setText(f"Gear: {self.current_gear}")
        runtime_secs = int(time.time() - self.start_time)
        mins, secs = divmod(runtime_secs, 60)
        self.runtime_label.setText(f"Run Time: {mins:02d}:{secs:02d}")

    def fast_update(self):
        if self.engine_stalled:
            self.current_rpm = 0
            self.current_speed = 0
            self.sim_throttle = 0
            self.current_throttle = 0
            self.current_load = 0
            self.turbo_boost = 0
            self.current_boost = 1
            self.update_display()
            return

        target_throttle = 100 if self.throttle_pressed else 0
        throttle_step = (target_throttle - self.sim_throttle) * 0.05
        self.sim_throttle += throttle_step
        self.sim_throttle = max(0, min(100, self.sim_throttle))
        self.update_sim_throttle(self.sim_throttle)

        idle_rpm = 750
        target_rpm = idle_rpm + (self.sim_throttle / 100) * (self.max_rpm - idle_rpm)
        rpm_step_factor = 0.1 if self.current_rpm < (self.max_rpm * 0.5) else 0.2
        rpm_step = (target_rpm - self.current_rpm) * rpm_step_factor

        stall_rpm = min(500, self.max_rpm * 0.1)
        if not self.clutch_pressed and self.sim_gear > 0 and self.current_rpm < stall_rpm:
            self.engine_stalled = True
            self.update_status()
            self.current_rpm = 0
            self.current_speed = 0
            self.sim_throttle = 0
        else:
            self.current_rpm += rpm_step
            self.current_rpm = max(idle_rpm if not self.engine_stalled else 0, min(self.max_rpm, self.current_rpm))

        gear_ratios = [3.8, 2.0, 1.4, 1.0, 0.8]
        final_drive = 4.0
        tire_circ = 2.0
        if self.clutch_pressed or self.sim_gear == 0:
            target_speed = 0
        else:
            target_speed = (self.current_rpm * tire_circ * 60) / (gear_ratios[self.sim_gear - 1] * final_drive * 1000)
            target_speed = (target_speed / 240) * self.max_speed
        speed_step = (target_speed - self.current_speed) * 0.05
        self.current_speed += speed_step
        self.current_speed = max(0, min(self.max_speed, self.current_speed))

        target_boost = min(1.5, max(-0.5, (self.sim_throttle / 100) * (self.current_rpm / self.max_rpm) * 1.5))
        boost_step = (target_boost - self.turbo_boost) * 0.03
        self.turbo_boost += boost_step
        self.turbo_boost = max(-0.5, min(1.5, self.turbo_boost))
        self.current_boost = 1 + self.turbo_boost

        self.current_throttle = self.sim_throttle
        load_base = (self.sim_throttle / 100) * 80
        load_adjust = (self.turbo_boost / 1.5) * 20
        self.current_load = load_base + load_adjust
        self.current_load = max(0, min(100, self.current_load))

        target_temp = 90 + (self.current_rpm / self.max_rpm) * 20
        temp_step = (target_temp - self.current_temp) * 0.01
        self.current_temp += temp_step
        self.current_temp = max(80, min(110, self.current_temp))

        self.update_display()

    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        gui = OBDGui()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")