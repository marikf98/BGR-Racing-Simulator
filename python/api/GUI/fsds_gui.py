import sys
import os
import tkinter as tk
from tkinter import ttk
import subprocess


class FSDS_GUI:
    def __init__(self, client, selected_fields, ALL_POTENTIAL_FIELDS):
        self.client = client
        self.selected_fields = selected_fields
        self.ALL_POTENTIAL_FIELDS = ALL_POTENTIAL_FIELDS
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
                    self.label_vars[field].set(str(self.ALL_POTENTIAL_FIELDS[field](data)))
                except Exception as e:
                    print(f"Error in field '{field}': {e}")
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
    
    
