"""
==============================================================
FSDS / AirSim settings.json Generator
==============================================================

This script creates a valid settings.json file for AirSim-based
Formula Student Driverless Simulator (FSDS) with GPS, IMU and LIDAR sensors.

📌 What it does:
- Takes a dictionary of sensor configurations
- Adds common parameters like `Enabled`, `RelativePosition`
- Writes everything into a valid settings.json file

✅ How to use:
1. Modify the `configurations` dictionary and/or "lidar_config"  to fit your sensor setup
2. Set the desired output path in `output_path`
3. Run this script 
4. Place the generated `settings.json` into your AirSim root folder
   (usually next to the `exe` of your simulator)

==============================================================
"""

import json

# Path to save the settings.json file
output_path = r"C:\Users\barak\PycharmProjects\BGR-Racing-Simulator\python\api\settings.json"  # Change this path if needed

# User-defined configuration for each sensor
configurations = {
    "GPS": {
        "enabled": True,                    # Whether to enable the GPS sensor
        "update_frequency": 10,             # GPS update rate in Hz
        "sensor_name": "Gps",               # The name used to refer to the sensor
        "vehicle_name": "FSCar",            # Name of the vehicle in AirSim
        "RelativePosition": [0.5, 0.0, 0.2]  # Relative position of the sensor on the car. [0, 0, 0] is the center of the car.
    },
    "IMU": {
        "enabled": True,                    # Whether to enable the IMU sensor
        "sensor_name": "Imu",               # The name used to refer to the sensor
        "vehicle_name": "FSCar",            # Name of the vehicle in AirSim
        "RelativePosition": [0.5, 0.0, 0.2]  # Relative position of the sensor on the car. [0, 0, 0] is the center of the car.
    }
}
# User-defined configuration specifically for Lidar senors
num_lidars = 6  # Amount of Lidars to be used in simulation

lidar_config = {
    "enabled": True,
    "vehicle_name": "FSCar",
    "SensorSettings": {
        "X": 1,
        "Y": 0,
        "Z": 0.5,
        "Roll": 0,
        "Pitch": -15,
        "Yaw": 0,
        "NumberOfLasers": 3,
        "PointsPerScan": 500,
        "VerticalFOVUpper": 0,
        "VerticalFOVLower": -7.5,
        "HorizontalFOVStart": -57.5,
        "HorizontalFOVEnd": 57.5,
        "RotationsPerSecond": 10,
        "DrawDebugPoints": True
    }
}

# Add lidar sensors to the configurations dictionary
for i in range(1, num_lidars + 1):
    name = "Lidar" if i == 1 else f"Lidar{i}"
    configurations[name] = {
        "enabled": lidar_config["enabled"],
        "sensor_name": name,
        "vehicle_name": lidar_config["vehicle_name"],
        "SensorSettings": lidar_config["SensorSettings"].copy()
    }

# Mapping from sensor type name to AirSim SensorType ID
SENSOR_TYPE_MAP = {
    "GPS": 3,   # GPS SensorType = 3 in AirSim
    "IMU": 2,    # IMU SensorType = 2 in AirSim
    "LIDAR": 6 # LIDAR SensorType = 6 in AirSim
}


def generate_settings_json(values_dict, output_path="settings.json"):
    sensors = {}
    vehicle_name = None

    for key, config in values_dict.items():
        name = config["sensor_name"]

        # Detect sensor type (Lidar vs others)
        if name.lower().startswith("lidar"):
            sensor_type = SENSOR_TYPE_MAP["LIDAR"]
        else:
            sensor_type = SENSOR_TYPE_MAP.get(key.upper(), 0)

        # Start building sensor block
        sensor_entry = {
            "SensorType": sensor_type,
            "Enabled": config["enabled"]
        }

        # Optional: add position if exists (for GPS/IMU)
        if "RelativePosition" in config:
            sensor_entry["RelativePosition"] = config["RelativePosition"]

        # Optional: update frequency for GPS
        if key.upper() == "GPS" and "update_frequency" in config:
            sensor_entry["update_frequency"] = config["update_frequency"]

        # Optional: Lidar-specific settings
        if "SensorSettings" in config:
            sensor_entry.update(config["SensorSettings"])

        sensors[name] = sensor_entry
        vehicle_name = config["vehicle_name"]

    # Create the full settings structure as required by AirSim
    settings = {
        "SettingsVersion": 1.2,
        "Vehicles": {
            vehicle_name: {
                "VehicleType": "PhysXCar",  # Default vehicle type in FSDS
                "AutoCreate": True,         # Automatically spawn the vehicle on startup
                "Sensors": sensors          # Add all sensors to this vehicle
            }
        }
    }

    # Write the settings to a JSON file
    with open(output_path, "w") as f:
        json.dump(settings, f, indent=4)

    print(f"✅ settings.json created successfully at: {output_path}")

# Run the function to generate settings.json
generate_settings_json(configurations, output_path)

output_path = "Path"
# User-defined configuration for each sensor
configurations = {
    "GPS": {
        "enabled": True,                    # Whether to enable the GPS sensor
        "update_frequency": 10,             # GPS update rate in Hz
        "sensor_name": "Gps",               # The name used to refer to the sensor
        "vehicle_name": "FSCar",            # Name of the vehicle in AirSim
        "RelativePosition": [0.5, 0.0, 0.2]  # Relative position of the sensor on the car
    },
    "IMU": {
        "enabled": True,                    # Whether to enable the IMU sensor
        "sensor_name": "Imu",               # The name used to refer to the sensor
        "vehicle_name": "FSCar",            # Name of the vehicle in AirSim
        "RelativePosition": [0.5, 0.0, 0.2]  # Relative position of the sensor on the car
    }
}

# Mapping from sensor type name to AirSim SensorType ID
SENSOR_TYPE_MAP = {
    "GPS": 3,   # GPS SensorType = 3 in AirSim
    "IMU": 2    # IMU SensorType = 2 in AirSim
}


def generate_settings_json(values_dict, output_path="settings.json"):
    sensors = {}         # Dictionary to store sensor configurations for settings.json
    vehicle_name = None  # Placeholder for vehicle name (assumed same for all sensors)

    # Loop through each sensor (e.g., GPS, IMU)
    for key, config in values_dict.items():
        name = config["sensor_name"]  # Sensor name to be used as key in JSON

        # Build the sensor entry with required fields
        sensor_entry = {
            "SensorType": SENSOR_TYPE_MAP.get(key.upper(), 0),  # Look up the sensor type ID
            "Enabled": config["enabled"],                       # Whether the sensor is enabled
            "RelativePosition": config["RelativePosition"]      # Sensor position
        }

        # Add update_frequency if provided (only for GPS at the moment)
        if key.upper() == "GPS" and "update_frequency" in config:
            sensor_entry["update_frequency"] = config["update_frequency"]

        # Add the sensor entry to the sensors dictionary
        sensors[name] = sensor_entry

        # Assume all sensors belong to the same vehicle
        vehicle_name = config["vehicle_name"]

    # Create the full settings structure as required by AirSim
    settings = {
        "SettingsVersion": 1.2,
        "Vehicles": {
            vehicle_name: {
                "VehicleType": "PhysXCar",  # Default vehicle type in FSDS
                "AutoCreate": True,         # Automatically spawn the vehicle on startup
                "Sensors": sensors          # Add all sensors to this vehicle
            }
        }
    }

    # Write the settings to a JSON file
    with open(output_path, "w") as f:
        json.dump(settings, f, indent=4)

    print(f"✅ settings.json created successfully at: {output_path}")

# Run the function to generate settings.json
generate_settings_json(configurations)
