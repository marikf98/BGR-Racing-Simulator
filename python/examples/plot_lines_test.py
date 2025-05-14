"""
This is a tiny autonomous system that should be able to finish a lap in an empty map with only cones. 
Use the following settings_orig.json:

{
  "SettingsVersion": 1.2,
  "Vehicles": {
    "FSCar": {
      "DefaultVehicleState": "",
      "EnableCollisionPassthrogh": false,
      "EnableCollisions": true,
      "AllowAPIAlways": true,
      "RC":{
          "RemoteControlID": -1
      },
      "Sensors": {
        "Gps" : {
          "SensorType": 3,
          "Enabled": true
        },
        "Lidar": {
          "SensorType": 6,
          "Enabled": true,
          "X": 1.3, "Y": 0, "Z": 0.1,
          "Roll": 0, "Pitch": 0, "Yaw" : 0,
          "NumberOfLasers": 1,
          "PointsPerScan": 500,
          "VerticalFOVUpper": 0,
          "VerticalFOVLower": 0,
          "HorizontalFOVStart": -90,
          "HorizontalFOVEnd": 90,
          "RotationsPerSecond": 10,
          "DrawDebugPoints": true
        }
      },
      "Cameras": {},
      "X": 0, "Y": 0, "Z": 0,
      "Pitch": 0, "Roll": 0, "Yaw": 0
    }
  }
}
"""

import sys
import os
import time

import numpy
import math
import matplotlib.pyplot as plt
import msgpack


## adds the fsds package located the parent directory to the pyhthon path
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
fsds_lib_path = r"D:\BGR Simulator\Simulator\Formula-Student-Driverless-Simulator-master\python"
sys.path.insert(0, fsds_lib_path)

import fsds

# connect to the simulator 
client = fsds.FSDSClient()

# Check network connection, exit if not connected
client.confirmConnection()
print("connection confirm")
# After enabling setting trajectory setpoints via the api. 
client.enableApiControl(True)

car_state = client.getCarState()
refereeState = client.getRefereeState()
print(car_state)
print(refereeState.cones)
# vector_point = fsds.Vector3r(4575.15283203125, 8130.01025390625, 2)
vector_point1 = fsds.Vector3r(10, 10, 45)
vector_point2 = fsds.Vector3r(20, 20, 45)

points_start = [vector_point1]
points_end = [vector_point2]
# points.append(refereeState.initial_position)
points = [fsds.Vector3r(10, 10, 45), fsds.Vector3r(15, 15, 45), fsds.Vector3r(20, 20, 45),fsds.Vector3r(25, 25, 45)]
# client.client.call('simPlotPoints', points, [1.0, 0.0, 0.0, 1.0], 10.0, -1.0, True)
# client.client.call('simPlotArrows', points_start,points_end, [1.0, 0.0, 0.0, 1.0], 5.0,2.0, -1.0, True)
client.client.call('simPlotLineStrip', points, [1.0, 0.0, 0.0, 1.0], 5.0, -1.0, True)

# lidar_data = fsds.LidarData.from_msgpack(client.client.call('getLidarData', '', "FSCar"))

plt.show()