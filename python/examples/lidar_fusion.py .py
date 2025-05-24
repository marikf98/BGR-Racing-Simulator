"""
This example shows how to retrieve lidar pointclouds.
It uses 7 lidars
Before running this you must add a lidar to your vehicle.
Add the following to your settings.json file in the Sensors section:

"ExampleLidar": {
    "SensorType": 6,
    "Enabled": true,
    "X": 1.3, "Y": 0, "Z": -0.3,
    "Roll": 0, "Pitch": 0, "Yaw" : 0,
    "NumberOfLasers": 15,
    "PointsPerScan": 4000,
    "VerticalFOVUpper": -5,
    "VerticalFOVLower": 5,
    "HorizontalFOVStart": -90,
    "HorizontalFOVEnd": 90,
    "RotationsPerSecond": 10,
    "DrawDebugPoints": true
}

"""
import random
import sys
import os
import time
import numpy as np
import numpy


yaw_angles = [
    np.deg2rad(-48.91),   # Lidar (center of -57.5 to -38.33)
    np.deg2rad(-28.75),   # Lidar2 (center of -38.33 to -19.16)
    np.deg2rad(-9.58),    # Lidar3 (center of -19.16 to 0)
    np.deg2rad(9.58),     # Lidar4 (center of 0 to 19.16)
    np.deg2rad(28.75),    # Lidar5 (center of 19.17 to 38.33)
    np.deg2rad(48.91)     # Lidar6 (center of 38.33 to 57.5)
]

# Transformation function for each LiDAR's point cloud
def transform_lidar_points(points, yaw_deg, pitch_deg=-5.0, roll_deg=0.0):
    """
    Transforms a LiDAR point cloud by applying yaw, pitch, and roll rotations.

    Args:
        points (np.ndarray): N x 3 array of LiDAR points [X, Y, Z].
        yaw_deg (float): Yaw angle in degrees.
        pitch_deg (float): Pitch angle in degrees.
        roll_deg (float): Roll angle in degrees.

    Returns:
        np.ndarray: Transformed N x 3 array of LiDAR points.
    """
    # Convert angles from degrees to radians
    yaw = np.deg2rad(yaw_deg)
    pitch = np.deg2rad(pitch_deg)
    roll = np.deg2rad(roll_deg)

    # Rotation matrices
    R_yaw = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw),  np.cos(yaw), 0],
        [0,            0,           1]
    ])

    R_pitch = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0,             1, 0           ],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])

    R_roll = np.array([
        [1, 0,            0           ],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll),  np.cos(roll)]
    ])

    # Combine rotations: Roll -> Pitch -> Yaw
    R = R_yaw @ R_pitch @ R_roll

    # Apply the rotation to the points
    return points @ R.T


def add_gaussian_noise(points, mean=0, variance=0.04 , clip_range=0.02):
    """
    Add Gaussian noise to a point cloud.

    Parameters:
        points (np.ndarray): Original points (n x 3).
        mean (float): Mean of the Gaussian noise.
        std_dev (float): Standard deviation of the noise.
        clip_range (float): Maximum absolute value of noise (in meters).

    Returns:
        np.ndarray: Noisy points.
    """
    std_dev = np.sqrt(variance)

    noise = np.random.normal(mean, std_dev, points.shape)
    if clip_range:
        noise = np.clip(noise, -clip_range, clip_range)
    return points + noise


## adds the fsds package located the parent directory to the pyhthon path
fsds_lib_path = r"C:\Users\amitk\Documents\GitHub\BGR-Racing-Simulator\python"
sys.path.insert(0, fsds_lib_path)
##TODO add your path to fsds directory in the prev line ^^^^^^^^^

import fsds

# connect to the AirSim simulator
client = fsds.FSDSClient()

# Check network connection
client.confirmConnection()

start_time = time.time()

lidardata = client.getLidarData(lidar_name = 'Lidar')
lidardata2 = client.getLidarData(lidar_name = 'Lidar2')
lidardata3 = client.getLidarData(lidar_name = 'Lidar3')
lidardata4 = client.getLidarData(lidar_name = 'Lidar4')
lidardata5 = client.getLidarData(lidar_name = 'Lidar5')
lidardata6 = client.getLidarData(lidar_name = 'Lidar6')
# lidardata7 = client.getLidarData(lidar_name = 'Lidar7')

point_list1 = lidardata.point_cloud
point_list2 = lidardata2.point_cloud
point_list3 = lidardata3.point_cloud
point_list4 = lidardata4.point_cloud
point_list5 = lidardata5.point_cloud
point_list6 = lidardata6.point_cloud
# point_list7 = lidardata6.point_cloud

# nanosecond timestamp of when the imu frame was captured
print("lidardata nano: ", lidardata.time_stamp)

# the location of the lidar at the moment of capture in global reference frame
print("lidar pose: ", lidardata.pose)

# Convert the list of floats into a list of xyz coordinates
points = numpy.array(point_list1, dtype=numpy.dtype('f4'))
points = numpy.reshape(points, (int(points.shape[0]/3), 3))
points = add_gaussian_noise(points, mean=0, variance=0.04 , clip_range=0.02)

# Convert the list of floats into a list of xyz coordinates
points2 = numpy.array(point_list2, dtype=numpy.dtype('f4'))
points2 = numpy.reshape(points2, (int(points2.shape[0]/3), 3))
points2 = add_gaussian_noise(points2, mean=0, variance=0.04 , clip_range=0.02)

# Convert the list of floats into a list of xyz coordinates
points3 = numpy.array(point_list3, dtype=numpy.dtype('f4'))
points3 = numpy.reshape(points3, (int(points3.shape[0]/3), 3))
points3 = add_gaussian_noise(points3, mean=0, variance=0.04 , clip_range=0.02)

# Convert the list of floats into a list of xyz coordinates
points4 = numpy.array(point_list4, dtype=numpy.dtype('f4'))
points4 = numpy.reshape(points4, (int(points4.shape[0]/3), 3))
points4 = add_gaussian_noise(points4, mean=0, variance=0.04 , clip_range=0.02)

# Convert the list of floats into a list of xyz coordinates
points5 = numpy.array(point_list5, dtype=numpy.dtype('f4'))
points5 = numpy.reshape(points5, (int(points5.shape[0]/3), 3))
points5 = add_gaussian_noise(points5, mean=0, variance=0.04 , clip_range=0.02)

# Convert the list of floats into a list of xyz coordinates
points6 = numpy.array(point_list6, dtype=numpy.dtype('f4'))
points6 = numpy.reshape(points6, (int(points6.shape[0]/3), 3))
points6 = add_gaussian_noise(points6, mean=0, variance=0.04 , clip_range=0.02)

# stacked_points = np.vstack((points, points2))
print("number of hit points: ", len(points))
print("number of hit points: ", len(points2))
print("number of hit points: ", len(points3))
print("number of hit points: ", len(points4))
print("number of hit points: ", len(points5))
print("number of hit points: ", len(points6))


mini_lidar_data = [points, points2, points3, points4, points5, points6]

# Define the yaw angles for each mini LiDAR (in radians)
# Assume the horizontal field of view is 115° divided into 6 segments
fov_horizontal = 115  # Total horizontal field of view in degrees
n_lidars = 7
overlap = 2



# Transform each mini LiDAR's data to the global frame
transformed_lidar_data = []
for mat, yaw in zip(mini_lidar_data, yaw_angles):
    transformed_points = transform_lidar_points(mat, yaw)
    transformed_lidar_data.append(transformed_points)


# Combine all transformed points into a single global matrix
global_lidar_data = np.vstack(transformed_lidar_data)

end_time = time.time()
elapsed_time = end_time - start_time
print(f"Execution time: {elapsed_time:.6f} seconds")


# Apply noise to your global LiDAR data
std_dev = 0.02  # 2 cm in meters
clip_range = 0.02  # Clip noise to ±2 cm

noisy_global_lidar_data = add_gaussian_noise(global_lidar_data, mean=0, variance=6, clip_range=clip_range)

# for point in points:
#     x = point[0]
#     y = point[1]
#     z = point[2]
#     # do something with these values

import open3d as o3d

# Create Open3D PointCloud object
point_cloud = o3d.geometry.PointCloud()
# point_cloud2 = o3d.geometry.PointCloud()

# Assign points to the point cloud object
point_cloud.points = o3d.utility.Vector3dVector(noisy_global_lidar_data )
# point_cloud2.points = o3d.utility.Vector3dVector(points2)
# Optionally: Set colors (if you have color data)
# colors = np.random.rand(num_points, 3)  # Random colors for each point
# point_cloud.colors = o3d.utility.Vector3dVector(colors)
rand = random.randint(1, 10000)
# Visualize the point cloud
o3d.visualization.draw_geometries([point_cloud])

o3d.io.write_point_cloud("C:\\Users\\amitk\\Formula-Student-Driverless-Simulator\\lidar_scans\\point_cloud_" + rand.__str__() + ".pcd", point_cloud)
# o3d.visualization.draw_geometries([point_cloud2])

