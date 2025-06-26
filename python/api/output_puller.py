import sys
import os
import time



# Add the fsds package located in the parent directory to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import fsds as fsds

# Configuration: Set to True to enable output for that field
PRINT_CONFIG = {
    # GPS fields
    "gps_timestamp_nano": True,
    "gps_timestamp_utc": True,
    "gps_eph": True,
    "gps_epv": True,
    "gps_geo_point": True,
    "gps_velocity": True,

    # IMU fields
    "imu_timestamp_nano": True,
    "imu_orientation": True,
    "imu_angular_velocity": True,
    "imu_linear_acceleration": True
}

# Connect to the AirSim simulator
client = fsds.FSDSClient()
client.confirmConnection()

while True:
    # --- GPS Data ---
    gps = client.getGpsData(gps_name='Gps', vehicle_name='FSCar')

    if PRINT_CONFIG["gps_timestamp_nano"]:
        print("[GPS] timestamp nano: ", gps.time_stamp)

    if PRINT_CONFIG["gps_timestamp_utc"]:
        print("[GPS] timestamp utc:  ", gps.gnss.time_utc)

    if PRINT_CONFIG["gps_eph"]:
        print("[GPS] eph (horiz error std dev): ", gps.gnss.eph)

    if PRINT_CONFIG["gps_epv"]:
        print("[GPS] epv (vert error std dev): ", gps.gnss.epv)

    if PRINT_CONFIG["gps_geo_point"]:
        print("[GPS] geo point (lat, long, alt): ", gps.gnss.geo_point)

    if PRINT_CONFIG["gps_velocity"]:
        print("[GPS] velocity (x, y, z m/s): ", gps.gnss.velocity)

    print()

    # --- IMU Data ---
    imu = client.getImuData(imu_name='Imu', vehicle_name='FSCar')

    if PRINT_CONFIG["imu_timestamp_nano"]:
        print("[IMU] timestamp nano: ", imu.time_stamp)

    if PRINT_CONFIG["imu_orientation"]:
        print("[IMU] orientation (rotation quaternion): ", imu.orientation)

    if PRINT_CONFIG["imu_angular_velocity"]:
        print("[IMU] angular velocity (rad/s): ", imu.angular_velocity)

    if PRINT_CONFIG["imu_linear_acceleration"]:
        print("[IMU] linear acceleration (m/s^2): ", imu.linear_acceleration)

    print("\n" + "-"*40 + "\n")
    time.sleep(1)
