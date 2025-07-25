# Journey Map Viewer

## Overview

The **Journey Map Viewer** is an interactive web application designed to visualise vehicle journey data from CSV files. It maps GPS coordinates with speed and RPM information, providing an intuitive way to analyse trips.

Users can upload their own journey data CSV files containing latitude, longitude, speed, and RPM readings, and view their journey on a Leaflet-based map. The journey is displayed as a polyline coloured by either speed or RPM, with tooltips showing detailed data for each segment. Additional statistics such as top speed, average speed, and total distance are also provided.

## Features

- **CSV File Upload:** Users upload their own journey data for custom visualisation.
- **Interactive Map:** Powered by Leaflet, showing the vehicle’s GPS path.
- **Colour Modes:**  
  - **Speed mode:** Colours the journey line in 10 km/h speed blocks (green to red spectrum).  
  - **RPM mode:** Colours the line from green to red based on RPM values (0 to 8000 rpm).
- **Tooltips:** Hovering over the journey line displays speed and RPM information dynamically following the cursor.
- **Start and End Markers:** Markers on the map highlight the journey's start and end coordinates, clickable for exact GPS values.
- **Legend and Stats:** Sidebar shows a legend for the current colour mode and statistics including top speed, average speed, and total distance travelled.
- **Zoom Control:** Reset zoom button to easily refocus on the entire journey.
- **Panning and Zoom Limits:** Users can pan and zoom around the journey area within sensible bounds.

## How to Use

1. Open the `index.html` file in a modern web browser.
2. Click the **Choose File** button to upload your journey CSV file.
3. Select the colour mode (`Speed` or `RPM`) from the dropdown.
4. View your journey plotted on the map, with the polyline coloured accordingly.
5. Hover over the polyline to see speed and RPM details.
6. Check the sidebar for the legend and trip statistics.
7. Use the **Reset Zoom** button to return the map view to the full journey.

## CSV File Format Requirements

The CSV file should have a header row and include at least the following columns:

- `lat` — Latitude (decimal degrees)  
- `lon` — Longitude (decimal degrees)  
- `speed` — Speed in km/h (numeric)  
- `rpm` — Engine RPM (numeric)  

Example CSV snippet:

timestamp,lat,lon,speed,rpm
2025-07-24T10:00:00Z,-36.8485,174.7633,50,3000
2025-07-24T10:00:05Z,-36.8480,174.7640,55,3200
...

## Complex Techniques Used

- **CSV Parsing and Dynamic Data Loading:** Uses the [PapaParse](https://www.papaparse.com/) library to parse user-uploaded CSV files client-side, extracting journey data dynamically.
- **Interactive Mapping with Leaflet:** Utilises the Leaflet.js library to render an interactive map with GPS coordinates, coloured polylines, tooltips, and markers.
- **Data Processing and Visualisation:**  
  - Colour-coding the polyline segments based on speed or RPM in defined blocks or gradients.  
  - Calculating and displaying statistics such as total distance (using geographic distance between points), average speed, and top speed.
- **Dynamic UI Elements:** Dropdown selectors and buttons control map behaviour and visualisation in real-time.

## Future Improvements (for later iterations)

- Export journey map or statistics to PDF or image format.
- Add more advanced analytics or data overlays.
- Allow user-defined thresholds for colour coding.
- Overall UI improvements