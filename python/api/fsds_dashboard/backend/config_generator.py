import json
import os

# Maps sensor names to AirSim SensorType IDs
SENSOR_TYPE_MAP = {
    "GPS": 3,
    "IMU": 2
}

DEFAULT_VEHICLE_TYPE = "PhysXCar"
DEFAULT_SETTINGS_PATH = os.path.join(os.getcwd(), "settings.json")


def generate_settings(values_dict: dict, output_path: str = DEFAULT_SETTINGS_PATH):
    sensors = {}
    vehicle_name = None

    for key, config in values_dict.items():
        name = config["sensor_name"]

        sensor_entry = {
            "SensorType": SENSOR_TYPE_MAP.get(key.upper(), 0),
            "Enabled": config["enabled"],
            "RelativePosition": config["RelativePosition"]
        }

        if key.upper() == "GPS" and "update_frequency" in config:
            sensor_entry["update_frequency"] = config["update_frequency"]

        sensors[name] = sensor_entry
        vehicle_name = config["vehicle_name"]

    settings = {
        "SettingsVersion": 1.2,
        "Vehicles": {
            vehicle_name: {
                "VehicleType": DEFAULT_VEHICLE_TYPE,
                "AutoCreate": True,
                "Sensors": sensors
            }
        }
    }

    with open(output_path, "w") as f:
        json.dump(settings, f, indent=4)

    print(f"✅ settings.json created successfully at: {output_path}")
