# This code adds the fsds package to the python path.
# Replace fsds_lib_path with the actual path where the python directory is located.
import sys, os

# Updated file path based on your given directory structure
fsds_lib_path = r"D:\BGR Simulator\Simulator\Formula-Student-Driverless-Simulator-master\python"
sys.path.insert(0, fsds_lib_path)

import time
import fsds

# connect to the AirSim simulator
client = fsds.FSDSClient()

# Check network connection
client.confirmConnection()

# After enabling api control, only the API can control the car.
# Direct keyboard and joystick input to the simulator are disabled.
# If you want to still be able to drive with the keyboard while also
# controlling the car using the API, call client.enableApiControl(False)
client.enableApiControl(True)

# Instruct the car to go full-speed forward
car_controls = fsds.CarControls()
car_controls.throttle = 1
client.setCarControls(car_controls)

time.sleep(5)

# Places the vehicle back at its original position
client.reset()
