import sys
import os
import tkinter as tk
from tkinter import ttk
import subprocess

# Add FSDS package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import fsds as fsds


# -------------------------- Formatting Helpers --------------------------
def format_vector3(v): return f"x: {v.x_val:.2f}, y: {v.y_val:.2f}, z: {v.z_val:.2f}"
def format_quaternion(q): return f"w: {q.w_val:.2f}, x: {q.x_val:.2f}, y: {q.y_val:.2f}, z: {q.z_val:.2f}"
def format_geo_point(g): return f"lat: {g.latitude:.5f}, lon: {g.longitude:.5f}, alt: {g.altitude:.2f}"

# -------------------------- Known Fields --------------------------
ALL_POTENTIAL_FIELDS = {
    "GPS Time (ns)": lambda data: data["gps"].time_stamp,
    "GPS UTC": lambda data: data["gps"].gnss.time_utc,
    "GPS Horizontal Accuracy": lambda data: f"{data['gps'].gnss.eph:.2f} m",
    "GPS Vertical Accuracy": lambda data: f"{data['gps'].gnss.epv:.2f} m",
    "GPS Location": lambda data: format_geo_point(data["gps"].gnss.geo_point),
    "GPS Velocity": lambda data: format_vector3(data["gps"].gnss.velocity),

    "IMU Time (ns)": lambda data: data["imu"].time_stamp,
    "IMU Orientation": lambda data: format_quaternion(data["imu"].orientation),
    "IMU Angular Velocity": lambda data: format_vector3(data["imu"].angular_velocity),
    "IMU Acceleration": lambda data: format_vector3(data["imu"].linear_acceleration),

    "LiDAR Time (ns)": lambda data: data["lidar"].time_stamp,
    "LiDAR Point Count": lambda data: len(data["lidar"].point_cloud) // 3
}

class FieldSelector:
    def __init__(self, client, available_fields):
        self.client = client
        self.available_fields = available_fields
        self.selected_fields = []
        self.window = tk.Tk()
        self.window.title("Select Telemetry Fields")

        tk.Label(self.window, text="Select fields to show:", font=("Segoe UI", 12, "bold")).pack(pady=10)

        self.check_vars = {}
        for field in available_fields:
            var = tk.BooleanVar(value=True)  # Default to selected
            self.check_vars[field] = var
            cb = ttk.Checkbutton(self.window, text=field, variable=var)
            cb.pack(anchor='w', padx=20)

        launch_button = ttk.Button(self.window, text="▶ Launch Dashboard", command=self.launch_dashboard)
        launch_button.pack(pady=20)

        self.window.mainloop()

    def launch_dashboard(self):
        self.selected_fields = [field for field, var in self.check_vars.items() if var.get()]
        self.window.destroy()
        FSDS_GUI(self.client, self.selected_fields)


class FSDS_GUI:
    def __init__(self, client, selected_fields):
        self.client = client
        self.selected_fields = selected_fields
        self.root = tk.Tk()
        self.root.title("FSDS Live Data")
        self.label_vars = {}
        self.script_process = None

        tk.Label(self.root, text="📡 FSDS Vehicle Telemetry", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(10, 20))

        for row_index, field in enumerate(self.selected_fields, start=1):
            tk.Label(self.root, text=field + ":", font=("Segoe UI", 10)).grid(
                row=row_index, column=0, sticky="e", padx=10, pady=5
            )
            var = tk.StringVar(value="Loading...")
            tk.Label(self.root, textvariable=var, font=("Courier New", 10)).grid(
                row=row_index, column=1, sticky="w", padx=10, pady=5
            )
            self.label_vars[field] = var

        # Script launcher
        self.script_path_var = tk.StringVar(value="run_my_script.py")
        tk.Label(self.root, text="Script Path:", font=("Segoe UI", 10)).grid(
            row=len(self.selected_fields) + 1, column=0, sticky="e", padx=10, pady=10)
        tk.Entry(self.root, textvariable=self.script_path_var, width=40).grid(
            row=len(self.selected_fields) + 1, column=1, sticky="w", padx=10, pady=10)

        ttk.Button(self.root, text="▶ Run Script", command=self.run_external_script).grid(
            row=len(self.selected_fields) + 2, column=0, sticky="e", padx=10, pady=(0, 15))
        self.stop_button = ttk.Button(self.root, text="⏹ Stop Script", command=self.stop_external_script, state="disabled")
        self.stop_button.grid(row=len(self.selected_fields) + 2, column=1, sticky="w", padx=10, pady=(0, 15))
        self.update_data()
        self.root.mainloop()

    def update_data(self):
        try:
            data = {}
            if any("GPS" in field for field in self.selected_fields):
                data["gps"] = self.client.getGpsData(gps_name="Gps", vehicle_name="FSCar")
            if any("IMU" in field for field in self.selected_fields):
                data["imu"] = self.client.getImuData(imu_name="Imu", vehicle_name="FSCar")
            if any("LiDAR" in field for field in self.selected_fields):
                data["lidar"] = self.client.getLidarData(lidar_name="Lidar", vehicle_name="FSCar")

            for field in self.selected_fields:
                try:
                    self.label_vars[field].set(str(ALL_POTENTIAL_FIELDS[field](data)))
                except:
                    self.label_vars[field].set("Error")
        except:
            for var in self.label_vars.values():
                var.set("Connection error")

        self.root.after(1000, self.update_data)

    def run_external_script(self):
        script_path = self.script_path_var.get().strip().strip('"')
        if not script_path:
            print("No script path provided.")
            return
        try:
            self.script_process = subprocess.Popen([sys.executable, script_path])
            print(f"Running: {script_path}")
            self.stop_button.config(state="normal")
        except Exception as e:
            print(f"Error running script: {e}")

    def stop_external_script(self):
        if self.script_process and self.script_process.poll() is None:
            try:
                self.script_process.terminate()
                self.script_process.wait(timeout=5)
                print("Script stopped.")
            except Exception as e:
                print(f"Error stopping script: {e}")
        else:
            print("No script is currently running.")
        self.script_process = None
        self.stop_button.config(state="disabled")
    
    


# ---------------------- App Entry Point ----------------------
if __name__ == "__main__":
    client = fsds.FSDSClient()
    client.confirmConnection()

    # Detect available fields
    test_data = {}
    available_fields = []
    try: test_data["gps"] = client.getGpsData(gps_name="Gps", vehicle_name="FSCar")
    except: pass
    try: test_data["imu"] = client.getImuData(imu_name="Imu", vehicle_name="FSCar")
    except: pass
    try: test_data["lidar"] = client.getLidarData(lidar_name="Lidar", vehicle_name="FSCar")
    except: pass

    for field, func in ALL_POTENTIAL_FIELDS.items():
        try:
            func(test_data)
            available_fields.append(field)
        except:
            continue

    FieldSelector(client, available_fields)
