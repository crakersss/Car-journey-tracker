# Vehicle Journey Visualiser

## Overview

This software project reads GPS, speed, and engine RPM data collected from a vehicle’s ECU (via an Arduino and OBD-II interface), saves the data to a CSV file, and displays it visually on an interactive map using Leaflet.js.

---

## What It Does

- Collects live vehicle data from an Arduino-based logger
- Stores journey data in a CSV file with GPS, speed, and RPM columns
- Displays the journey path on a map using Leaflet.js
- Each data point is plotted using latitude and longitude coordinates
- Basic features include map zooming, panning, and a polyline showing the route

---

## Technology Stack

### **Software:**
- **Python (PyQt5)** – GUI for starting/stopping data logging
- **Arduino** – Reads GPS and ECU data from the vehicle and sends it over USB
- **JavaScript + Leaflet.js** – Displays the journey on a browser-based map

### **Hardware:**
- Arduino Nano + OBD-II Adapter (MCP2515/2551)
- GPS Module (e.g. Neo-6M)
- Laptop or PC running Python and browser to view the output

---

## CSV Data Format

Each line of the CSV includes:

```csv
timestamp,latitude,longitude,speed,rpm
2025-07-23 10:03:21,-36.91075,174.87658,49.5,2300

