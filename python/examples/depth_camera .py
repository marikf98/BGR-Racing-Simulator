"""
###This example shows how to retrieve a color image and store it as a png file
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
import random
import math

## adds the fsds package located the parent directory to the pyhthon path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import fsds

# connect to the simulator
client = fsds.FSDSClient()

# Check network connection, exit if not connected
client.confirmConnection()

def DepthConversion(PointDepth, f):
    H = PointDepth.shape[0]
    W = PointDepth.shape[1]
    i_c = float(H) / 2 - 1
    j_c = float(W) / 2 - 1
    columns, rows = np.meshgrid(np.linspace(0, W-1, num=W), np.linspace(0, H-1, num=H))
    DistanceFromCenter = ((rows - i_c)**2 + (columns - j_c)**2)**(0.5)
    PlaneDepth = PointDepth / (1 + (DistanceFromCenter / f)**2)**(0.5)
    return PlaneDepth


# Fetch depth image
responses = client.simGetImages([fsds.ImageRequest(camera_name='Camera1', image_type=fsds.ImageType.DepthPerspective,
                                                   pixels_as_float=True, compress=False)], vehicle_name='FSCar')
response = responses[0]
width = response.width
fov_rad = math.radians(90)  # Assuming 90° HFOV
Fx = Fy = width / (2 * math.tan(fov_rad / 2))
img1d = np.array(response.image_data_float, dtype=np.float32)
img1d[img1d > 255] = 255
img2d = np.reshape(img1d, (responses[0].height, responses[0].width))
img2d_converted = DepthConversion(img2d, Fx)


# Create 3D points
H, W = img2d_converted.shape
i_c, j_c = H // 2 - 1, W // 2 - 1  # Image center
u, v = np.meshgrid(np.arange(W), np.arange(H))  # Pixel coordinates
z = img2d_converted
x = (u - j_c) * z / Fx
y = (v - i_c) * z / Fy

# Stack into Nx3 array
points = np.stack((x.flatten(), y.flatten(), z.flatten()), axis=-1)




import open3d as o3d

# Create Open3D PointCloud object
point_cloud = o3d.geometry.PointCloud()
# point_cloud2 = o3d.geometry.PointCloud()

# Assign points to the point cloud object
point_cloud.points = o3d.utility.Vector3dVector(points)
# point_cloud2.points = o3d.utility.Vector3dVector(points2)
# Optionally: Set colors (if you have color data)
# colors = np.random.rand(num_points, 3)  # Random colors for each point
# point_cloud.colors = o3d.utility.Vector3dVector(colors)
rand = random.randint(1, 10000)
# Visualize the point cloud
o3d.visualization.draw_geometries([point_cloud])




# Check if the response contains valid data
if response.pixels_as_float:
    # Convert depth data to a NumPy array
    depth_data = np.array(response.image_data_float, dtype=np.float32)
    # Reshape to match image dimensions
    depth_image = depth_data.reshape(response.height, response.width)

    # Normalize depth data for visualization (optional)
    depth_image_normalized = cv2.normalize(depth_image, None, 0, 255, cv2.NORM_MINMAX)
    depth_image_normalized = depth_image_normalized.astype(np.uint8)

    resized_depth_image = cv2.resize(depth_image_normalized, (1024, 768), interpolation=cv2.INTER_LINEAR)

    # Display the image
    cv2.imshow("Resized Depth View", resized_depth_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("Depth image retrieval failed or not in the expected format.")
