import time
import random

# In production, this would connect to FSDS (AirSim) via Python client
# For now, we'll simulate GPS and IMU data

def get_latest_sensor_data():
    # Simulated GPS data
    gps_data = {
        "latitude": 32.1234 + random.uniform(-0.0001, 0.0001),
        "longitude": 34.5678 + random.uniform(-0.0001, 0.0001),
        "altitude": 100 + random.uniform(-0.5, 0.5),
        "velocity": {
            "x": random.uniform(-1, 1),
            "y": random.uniform(-1, 1),
            "z": random.uniform(-0.2, 0.2)
        },
        "timestamp": int(time.time() * 1000)
    }

    # Simulated IMU data
    imu_data = {
        "acceleration": {
            "x": random.uniform(-2, 2),
            "y": random.uniform(-2, 2),
            "z": random.uniform(-2, 2)
        },
        "angular_velocity": {
            "x": random.uniform(-1, 1),
            "y": random.uniform(-1, 1),
            "z": random.uniform(-1, 1)
        },
        "timestamp": int(time.time() * 1000)
    }

    return {
        "GPS": gps_data,
        "IMU": imu_data
    }
