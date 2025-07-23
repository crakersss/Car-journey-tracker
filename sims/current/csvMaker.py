import requests
import polyline
import csv
from datetime import datetime, timedelta
import random

# Your start and end coordinates (lat, lon)
start = (-36.909211, 174.876973)  # Example coordinate
end = (-36.891172, 174.932592)    # Example coordinate

# OSRM API endpoint
url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=polyline"

response = requests.get(url)
data = response.json()

if 'routes' not in data or len(data['routes']) == 0:
    print("No route found!")
    exit()

# Decode the polyline geometry into a list of (lat, lon) points
route_polyline = data['routes'][0]['geometry']
route_points = polyline.decode(route_polyline)  # returns list of (lat, lon)

# Simulate speed around 50 km/h with some variation
def simulate_speed():
    return max(40, min(60, random.gauss(50, 4)))

# Simulate RPM based on speed
def simulate_rpm(speed):
    base_rpm = 800
    rpm = base_rpm + (speed * 50) + random.uniform(-100, 100)
    return int(max(700, min(4000, rpm)))

# Generate timestamps spaced 1 second apart
start_time = datetime.now()

csv_data = []
for i, (lat, lon) in enumerate(route_points):
    timestamp = (start_time + timedelta(seconds=i)).strftime('%Y-%m-%d %H:%M:%S')
    speed = round(simulate_speed(), 1)
    rpm = simulate_rpm(speed)
    csv_data.append([timestamp, rpm, speed, lat, lon])

# Save to CSV file
filename = "osrm_route_journey.csv"
with open(filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['timestamp', 'rpm', 'speed', 'lat', 'lon'])
    writer.writerows(csv_data)

print(f"Route saved to {filename}")
