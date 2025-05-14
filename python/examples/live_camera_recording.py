"""
###This example shows a live steam of the camera during a drive
Before running this you must add the camera to your vehicle.
Add the following to your settings.json file in the Cameras section:

"examplecam": {
    "CaptureSettings": [
    {
        "ImageType": 0,
        "Width": 785,
        "Height": 785,
        "FOV_Degrees": 90
    }
    ],
    "X": 1.0,
    "Y": 0.06,
    "Z": -1.20,
    "Pitch": 0.0,
    "Roll": 0.0,
    "Yaw": 0
},

"""

import sys
import os
import cv2
import numpy as np


## adds the fsds package located the parent directory to the pyhthon path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import fsds

# connect to the simulator
client = fsds.FSDSClient()

# Check network connection, exit if not connected
client.confirmConnection()

#Loop to capture and display images continuously
while True:
    # Capture an image from the simulator
    [image] = client.simGetImages([fsds.ImageRequest(camera_name='examplecam', image_type=fsds.ImageType.Scene,
                                                     pixels_as_float=False, compress=False)], vehicle_name='FSCar')

    # Convert the image data to a NumPy array and reshape it for OpenCV
    img_data = np.frombuffer(image.image_data_uint8, dtype=np.uint8)
    img = img_data.reshape(image.height, image.width, 3)

    # Display the image using OpenCV
    cv2.imshow("Simulator View", img)

    # Check for a key press to break the loop (e.g., press 'q' to quit)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources and close OpenCV windows
cv2.destroyAllWindows()