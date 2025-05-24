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
import open3d as o3d


## adds the fsds package located the parent directory to the pyhthon path
sys.path.insert(0, r"C:\Users\amitk\Documents\GitHub\BGR-Racing-Simulator\python")
##TODO add your path to fsds directory in the prev line ^^^^^^^^^
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

def add_gaussian_noise(points, mean=0, variance=0.04 , clip_range=0.02):
    std_dev = np.sqrt(variance)
    noise = np.random.normal(mean, std_dev, points.shape)
    if clip_range:
        noise = np.clip(noise, -clip_range, clip_range)
    return points + noise


# # display 2D depth camera in color scale
# # Depth clipping range (in meters)
# min_depth = 1
# max_depth = 15
#
# while True:
#     # Fetch depth image
#     responses = client.simGetImages([
#         fsds.ImageRequest(camera_name='DepthCamera',
#                           image_type=fsds.ImageType.DepthPerspective,
#                           pixels_as_float=True,
#                           compress=False)], vehicle_name='FSCar')
#
#     if responses and responses[0].height > 0:
#         response = responses[0]
#         depth_img = np.array(response.image_data_float, dtype=np.float32)
#         depth_img = depth_img.reshape(response.height, response.width)
#
#         # Clip depth values to avoid skewing visualization
#         depth_img = np.clip(depth_img, min_depth, max_depth)
#
#         # Normalize depth to 0–255
#         depth_normalized = 255 * (1-(depth_img - min_depth) / (max_depth - min_depth))
#         depth_uint8 = depth_normalized.astype(np.uint8)
#
#         # Apply color map
#         depth_colored = cv2.applyColorMap(depth_uint8, cv2.COLORMAP_JET)
#
#         # Show the image
#         cv2.imshow("Depth Image (Color)", depth_uint8)
#
#         # Press 'q' to quit
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
#     else:
#         print("Failed to get depth image.")
#
# cv2.destroyAllWindows()

responses = client.simGetImages([
        fsds.ImageRequest(camera_name='DepthCamera',
                          image_type=fsds.ImageType.DepthPerspective,
                          pixels_as_float=True,
                          compress=False)], vehicle_name='FSCar')

response = responses[0]
width = response.width
fov_rad = math.radians(90)  # Assuming 90° HFOV
Fx = Fy = width / (2 * math.tan(fov_rad / 2))
img1d = np.array(response.image_data_float, dtype=np.float32)
max_range = 50
img1d[img1d > max_range] = max_range
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
# Apply noise to your global LiDAR data
std_dev = 0.02  # 2 cm in meters
clip_range = 0.02  # Clip noise to ±2 cm
points = np.stack((x.flatten(), y.flatten(), z.flatten()), axis=-1)
noisy_global_data = add_gaussian_noise(points, mean=0, variance=6, clip_range=clip_range)


import open3d as o3d

# Create Open3D PointCloud object
point_cloud = o3d.geometry.PointCloud()
# point_cloud2 = o3d.geometry.PointCloud()

# Assign points to the point cloud object
point_cloud.points = o3d.utility.Vector3dVector(noisy_global_data)
# point_cloud2.points = o3d.utility.Vector3dVector(points2)
# Optionally: Set colors (if you have color data)
# colors = np.random.rand(num_points, 3)  # Random colors for each point
# point_cloud.colors = o3d.utility.Vector3dVector(colors)
rand = random.randint(1, 10000)
# Visualize the point cloud
o3d.visualization.draw_geometries([point_cloud])






