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
def format_point2d(point):return f"({point.x:.2f}, {point.y:.2f})"

# -------------------------- Known Fields --------------------------
ALL_POTENTIAL_FIELDS = {
    # GPS
    "GPS Time (ns)": lambda data: data["gps"].time_stamp,
    "GPS UTC": lambda data: data["gps"].gnss.time_utc,
    "GPS Horizontal Accuracy": lambda data: f"{data['gps'].gnss.eph:.2f} m",
    "GPS Vertical Accuracy": lambda data: f"{data['gps'].gnss.epv:.2f} m",
    "GPS Location": lambda data: format_geo_point(data["gps"].gnss.geo_point),
    "GPS Velocity": lambda data: format_vector3(data["gps"].gnss.velocity),

    # IMU
    "IMU Time (ns)": lambda data: data["imu"].time_stamp,
    "IMU Orientation": lambda data: format_quaternion(data["imu"].orientation),
    "IMU Angular Velocity": lambda data: format_vector3(data["imu"].angular_velocity),
    "IMU Acceleration": lambda data: format_vector3(data["imu"].linear_acceleration),

    # LiDAR
    "LiDAR Time (ns)": lambda data: data["lidar"].time_stamp,
    "LiDAR Point Count": lambda data: len(data["lidar"].point_cloud) // 3,
    "LiDAR Pose": lambda data: f"Pos: {format_vector3(data['lidar'].pose.position)}, Ori: {format_quaternion(data['lidar'].pose.orientation)}",

    # Ground Speed Sensor
    "Ground Speed Time (ns)": lambda data: data["ground_speed"].time_stamp,
    "Ground Speed Linear Velocity": lambda data: format_vector3(data["ground_speed"].linear_velocity),

    # Car State
    "Car Timestamp (ns)": lambda data: data["car_state"].timestamp,
    "Car Speed (m/s)": lambda data: f"{data['car_state'].speed:.2f} m/s",
    "Car Estimated Position": lambda data: format_vector3(data["car_state"].kinematics_estimated.position),
    "Car Estimated Orientation": lambda data: format_quaternion(data["car_state"].kinematics_estimated.orientation),
    "Car Estimated Linear Velocity": lambda data: format_vector3(data["car_state"].kinematics_estimated.linear_velocity),
    "Car Estimated Angular Velocity": lambda data: format_vector3(data["car_state"].kinematics_estimated.angular_velocity),
    "Car Estimated Linear Acceleration": lambda data: format_vector3(data["car_state"].kinematics_estimated.linear_acceleration),
    "Car Estimated Angular Acceleration": lambda data: format_vector3(data["car_state"].kinematics_estimated.angular_acceleration),



    # Collision Info (from Car State)
    "Collision Detected": lambda data: data["car_state"].collision.has_collided,
    "Collision Impact Point": lambda data: format_vector3(data["car_state"].collision.impact_point),
    "Collision Normal": lambda data: format_vector3(data["car_state"].collision.normal),
    "Collision Penetration Depth": lambda data: f"{data['car_state'].collision.penetration_depth:.3f}",
    "Collision Object Name": lambda data: data["car_state"].collision.object_name,
    "Collision Time Stamp": lambda data: data["car_state"].collision.time_stamp,

    # Referee State
    "Referee DOO Counter": lambda data: data["referee"].doo_counter,
    "Referee Laps": lambda data: data["referee"].laps,
    "Referee Initial Position": lambda data: format_point2d(data["referee"].initial_position),
    "Referee Cone Count": lambda data: len(data["referee"].cones),

}

ALWAYS_AVAILABLE_FIELDS = [
    # Car State
    "Car Timestamp (ns)",
    "Car Speed (m/s)",
    "Car Estimated Position",
    "Car Estimated Orientation",
    "Car Estimated Linear Velocity",
    "Car Estimated Angular Velocity",
    "Car Estimated Linear Acceleration",
    "Car Estimated Angular Acceleration",

    # Collision Info (may be initialized to default values)
    "Collision Detected",
    "Collision Impact Point",
    "Collision Normal",
    "Collision Penetration Depth",
    "Collision Object Name",
    "Collision Time Stamp",

    # Referee State
    "Referee DOO Counter",
    "Referee Laps",
    "Referee Initial Position",
    "Referee Cone Count",
]



# ---------------------- App Entry Point ----------------------


if __name__ == "__main__":
    client = fsds.FSDSClient()
    client.confirmConnection()

    # Try to collect test data from sensors
    test_data = {}
    try: test_data["gps"] = client.getGpsData(gps_name="Gps", vehicle_name="FSCar")
    except: pass
    try: test_data["imu"] = client.getImuData(imu_name="Imu", vehicle_name="FSCar")
    except: pass
    try: test_data["lidar"] = client.getLidarData(lidar_name="Lidar", vehicle_name="FSCar")
    except: pass

    # Detect which fields are working
    available_fields = []
    for field, func in ALL_POTENTIAL_FIELDS.items():
        # If it's in the always-available list → add it without checking
        if field in ALWAYS_AVAILABLE_FIELDS:
            available_fields.append(field)
            continue

        # Otherwise, try to test it
        try:
            func(test_data)
            available_fields.append(field)
        except:
            continue

    # Pass the available fields to the GUI
    field_selector = FieldSelector(client, available_fields)

    FSDS_GUI(
        client,
        field_selector.selected_fields,
        ALL_POTENTIAL_FIELDS,
        field_selector.print_to_terminal,
        field_selector.save_to_csv
    )
