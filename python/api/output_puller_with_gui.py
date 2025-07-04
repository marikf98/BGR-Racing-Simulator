import sys
import os
import tkinter as tk
from tkinter import ttk
import subprocess


# Add FSDS package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from python import fsds
from api import GUI

from GUI import FieldSelector, FSDS_GUI


# -------------------------- Formatting Helpers --------------------------
def format_vector3(v): return f"x: {v.x_val:.2f}, y: {v.y_val:.2f}, z: {v.z_val:.2f}"
def format_quaternion(q): return f"w: {q.w_val:.2f}, x: {q.x_val:.2f}, y: {q.y_val:.2f}, z: {q.z_val:.2f}"
def format_geo_point(g): return f"lat: {g.latitude:.5f}, lon: {g.longitude:.5f}, alt: {g.altitude:.2f}"

# -------------------------- Known Fields --------------------------
ALL_POTENTIAL_FIELDS = {
    "GPS Time (ns)": lambda data: data["gps"].time_stamp,
    "GPS UTC": lambda data: data["gps"].gnss.time_utc,
    "GPS Horizontal Accuracy": lambda data: f"{data['gps'].gnss.eph:.2f} m",
    "GPS Vertical Accuracy": lambda data: f"{data['gps'].gnss.epv:.2f} m",
    "GPS Location": lambda data: format_geo_point(data["gps"].gnss.geo_point),
    "GPS Velocity": lambda data: format_vector3(data["gps"].gnss.velocity),

    "IMU Time (ns)": lambda data: data["imu"].time_stamp,
    "IMU Orientation": lambda data: format_quaternion(data["imu"].orientation),
    "IMU Angular Velocity": lambda data: format_vector3(data["imu"].angular_velocity),
    "IMU Acceleration": lambda data: format_vector3(data["imu"].linear_acceleration),

    "LiDAR Time (ns)": lambda data: data["lidar"].time_stamp,
    "LiDAR Point Count": lambda data: len(data["lidar"].point_cloud) // 3
}





# ---------------------- App Entry Point ----------------------
if __name__ == "__main__":
    client = fsds.FSDSClient()
    client.confirmConnection()

    # Detect available fields
    test_data = {}
    available_fields = []
    try: test_data["gps"] = client.getGpsData(gps_name="Gps", vehicle_name="FSCar")
    except: pass
    try: test_data["imu"] = client.getImuData(imu_name="Imu", vehicle_name="FSCar")
    except: pass
    try: test_data["lidar"] = client.getLidarData(lidar_name="Lidar", vehicle_name="FSCar")
    except: pass

    for field, func in ALL_POTENTIAL_FIELDS.items():
        try:
            func(test_data)
            available_fields.append(field)
        except:
            continue

    field_selector = FieldSelector(client, available_fields)

    FSDS_GUI(client, field_selector.selected_fields, ALL_POTENTIAL_FIELDS)
