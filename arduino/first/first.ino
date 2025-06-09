#include <TinyGPS++.h>
#include <SoftwareSerial.h>

// GPS setup
const int RX_PIN = 6, TX_PIN = 5;
const uint32_t GPS_BAUD = 9600;
TinyGPSPlus gps;
SoftwareSerial gpsSerial(RX_PIN, TX_PIN);

void setup() {
  Serial.begin(115200);
  while (!Serial) ; // Wait for Serial

  // Initialize GPS
  gpsSerial.begin(GPS_BAUD);
  Serial.println("NEO-6M GPS Initialized");

  // CSV header
  Serial.println("timestamp,rpm,speed,lat,lon");
}

void loop() {
  unsigned long timestamp = millis();
  double lat = 0.0, lon = 0.0;

  // Read GPS data
  while (gpsSerial.available() > 0) {
    if (gps.encode(gpsSerial.read()) && gps.location.isValid()) {
      lat = gps.location.lat();
      lon = gps.location.lng();
    }
  }

  // Mock OBD-II data (replace with real data later)
  float rpm = 3000; // Mock value
  float speed = 60; // Mock value

  // Log to Serial
  Serial.print(timestamp);
  Serial.print(",");
  Serial.print(rpm);
  Serial.print(",");
  Serial.print(speed);
  Serial.print(",");
  Serial.print(lat, 6);
  Serial.print(",");
  Serial.println(lon, 6);

  delay(500); // Log every 500ms
}