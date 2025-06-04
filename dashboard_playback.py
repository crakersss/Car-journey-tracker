import sys
import warnings
import pandas as pd
import os
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QFileDialog,
)
from PyQt5.QtCore import Qt, QTimer
from qroundprogressbar import QRoundProgressBar

# Suppress sip warning
warnings.filterwarnings("ignore", category=DeprecationWarning, message="sipPyTypeDict.*")

class OBDViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.max_rpm = 8000
        self.max_speed = 240
        self.current_rpm = 0
        self.current_speed = 0
        self.current_temp = 90
        self.current_throttle = 0
        self.current_load = 0
        self.current_boost = 0
        self.current_gear = "N"
        self.data = None
        self.current_index = 0
        self.init_ui()

        self.replay_timer = QTimer(self)
        self.replay_timer.timeout.connect(self.update_display)
        self.show()

    def init_ui(self):
        self.setWindowTitle("Car Journey Viewer")
        self.setGeometry(100, 100, 800, 700)

        main_layout = QVBoxLayout()

        self.status_label = QLabel("Select a journey CSV to visualize")
        main_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

        top_gauge_layout = QHBoxLayout()

        rpm_container = QVBoxLayout()
        self.rpm_title = QLabel("Engine RPM")
        self.rpm_title.setAlignment(Qt.AlignCenter)
        rpm_container.addWidget(self.rpm_title)
        self.rpm_gauge = QRoundProgressBar()
        self.rpm_gauge.setMinimum(0)
        self.rpm_gauge.setMaximum(self.max_rpm)
        self.rpm_gauge.setValue(0)
        self.rpm_gauge.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.rpm_gauge.setFixedSize(260, 260)
        self.rpm_gauge.setDataPenWidth(10)
        self.rpm_gauge.setFormat("%v RPM")
        rpm_container.addWidget(self.rpm_gauge, alignment=Qt.AlignCenter)
        top_gauge_layout.addLayout(rpm_container)

        speed_container = QVBoxLayout()
        self.speed_title = QLabel("Vehicle Speed")
        self.speed_title.setAlignment(Qt.AlignCenter)
        speed_container.addWidget(self.speed_title)
        self.speed_gauge = QRoundProgressBar()
        self.speed_gauge.setMinimum(0)
        self.speed_gauge.setMaximum(self.max_speed)
        self.speed_gauge.setValue(0)
        self.speed_gauge.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.speed_gauge.setFixedSize(260, 260)
        self.speed_gauge.setDataPenWidth(10)
        self.speed_gauge.setFormat("%v km/h")
        speed_container.addWidget(self.speed_gauge, alignment=Qt.AlignCenter)
        top_gauge_layout.addLayout(speed_container)
        main_layout.addLayout(top_gauge_layout)

        mid_gauge_layout = QHBoxLayout()

        self.load_title = QLabel("Engine Load")
        mid_gauge_layout.addWidget(self.load_title, alignment=Qt.AlignCenter)
        self.load_gauge = QRoundProgressBar()
        self.load_gauge.setMinimum(0)
        self.load_gauge.setMaximum(100)
        self.load_gauge.setValue(0)
        self.load_gauge.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.load_gauge.setFixedSize(120, 120)
        self.load_gauge.setDataPenWidth(6)
        self.load_gauge.setFormat("%v %")
        mid_gauge_layout.addWidget(self.load_gauge, alignment=Qt.AlignCenter)

        self.boost_title = QLabel("Boost Pressure")
        mid_gauge_layout.addWidget(self.boost_title, alignment=Qt.AlignCenter)
        self.boost_gauge = QRoundProgressBar()
        self.boost_gauge.setMinimum(0)
        self.boost_gauge.setMaximum(3)
        self.boost_gauge.setValue(1)
        self.boost_gauge.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.boost_gauge.setFixedSize(120, 120)
        self.boost_gauge.setDataPenWidth(6)
        self.boost_gauge.setFormat("%.1f bar")
        mid_gauge_layout.addWidget(self.boost_gauge, alignment=Qt.AlignCenter)

        main_layout.addLayout(mid_gauge_layout)

        self.throttle_title = QLabel("Throttle Position")
        main_layout.addWidget(self.throttle_title, alignment=Qt.AlignCenter)
        self.throttle_bar = QProgressBar()
        self.throttle_bar.setMinimum(0)
        self.throttle_bar.setMaximum(100)
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
        main_layout.addWidget(self.throttle_bar, alignment=Qt.AlignCenter)

        self.temp_title = QLabel("Coolant Temperature")
        main_layout.addWidget(self.temp_title, alignment=Qt.AlignCenter)
        self.temp_bar = QProgressBar()
        self.temp_bar.setMinimum(0)
        self.temp_bar.setMaximum(150)
        self.temp_bar.setValue(90)
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
        main_layout.addWidget(self.temp_bar, alignment=Qt.AlignCenter)

        self.rpm_label = QLabel("RPM: 0")
        main_layout.addWidget(self.rpm_label, alignment=Qt.AlignCenter)

        self.speed_label = QLabel("Speed: 0 km/h")
        main_layout.addWidget(self.speed_label, alignment=Qt.AlignCenter)

        self.throttle_label = QLabel("Throttle: 0 %")
        main_layout.addWidget(self.throttle_label, alignment=Qt.AlignCenter)

        self.temp_label = QLabel("Temp: 90 °C")
        main_layout.addWidget(self.temp_label, alignment=Qt.AlignCenter)

        self.gear_label = QLabel("Gear: N")
        main_layout.addWidget(self.gear_label, alignment=Qt.AlignCenter)

        self.runtime_label = QLabel("Run Time: 00:00")
        main_layout.addWidget(self.runtime_label, alignment=Qt.AlignCenter)

        # Upload button
        self.upload_button = QPushButton("Upload Journey CSV")
        self.upload_button.clicked.connect(self.upload_csv)
        main_layout.addWidget(self.upload_button, alignment=Qt.AlignCenter)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        main_layout.addWidget(self.exit_button)

        self.setLayout(main_layout)

    def upload_csv(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV File",
            os.path.expanduser("~"),
            "CSV Files (*.csv);;All Files (*)"
        )
        if filepath:
            try:
                self.data = pd.read_csv(filepath)
                self.current_index = 0
                self.status_label.setText("Playing journey...")
                self.replay_timer.start(500)  # Replay at 500ms intervals
            except Exception as e:
                self.status_label.setText(f"Error loading CSV: {e}")

    def update_display(self):
        if self.data is None or self.current_index >= len(self.data):
            self.replay_timer.stop()
            self.status_label.setText("Journey playback finished. Upload another CSV.")
            return

        row = self.data.iloc[self.current_index]
        self.current_rpm = int(row["rpm"])
        self.current_speed = int(row["speed"])
        self.current_throttle = int(row["throttle"])
        self.current_temp = int(row["temp"])
        self.current_load = int(row["load"])
        self.current_boost = float(row["boost"])
        self.current_gear = str(row["gear"])

        self.rpm_gauge.setValue(self.current_rpm)
        self.rpm_label.setText(f"RPM: {self.current_rpm}")
        self.speed_gauge.setValue(self.current_speed)
        self.speed_label.setText(f"Speed: {self.current_speed} km/h")
        self.throttle_bar.setValue(self.current_throttle)
        self.throttle_label.setText(f"Throttle: {self.current_throttle} %")
        self.temp_bar.setValue(self.current_temp)
        self.temp_label.setText(f"Temp: {self.current_temp} °C")
        self.load_gauge.setValue(self.current_load)
        self.boost_gauge.setValue(self.current_boost)
        self.gear_label.setText(f"Gear: {self.current_gear}")

        runtime_secs = int(row["timestamp"])
        mins, secs = divmod(runtime_secs, 60)
        self.runtime_label.setText(f"Run Time: {mins:02d}:{secs:02d}")

        self.current_index += 1

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = OBDViewer()
    sys.exit(app.exec())