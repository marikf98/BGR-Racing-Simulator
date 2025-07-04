import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import csv
import datetime


class FSDS_GUI:
    def __init__(self, client, selected_fields, ALL_POTENTIAL_FIELDS, print_to_terminal=False, save_to_csv=False):
        # Store initialization parameters
        self.client = client
        self.selected_fields = selected_fields
        self.ALL_POTENTIAL_FIELDS = ALL_POTENTIAL_FIELDS
        self.print_to_terminal = print_to_terminal
        self.save_to_csv = save_to_csv

        # Initialize the main window
        self.root = tk.Tk()
        self.root.title("FSDS Live Data")
        self.label_vars = {}  # Store StringVars for each field
        self.script_process = None  # For external script execution

        # CSV file setup (create file and write headers if saving is enabled)
        self.csv_file = None
        self.csv_writer = None
        if self.save_to_csv:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.csv_file = open(f"telemetry_{timestamp}.csv", mode="w", newline="")
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow(["Timestamp"] + self.selected_fields)

        # Title label
        tk.Label(self.root, text="📡 FSDS Vehicle Telemetry", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(10, 20)
        )

        # Create labels for each selected telemetry field
        for row_index, field in enumerate(self.selected_fields, start=1):
            tk.Label(self.root, text=field + ":", font=("Segoe UI", 10)).grid(
                row=row_index, column=0, sticky="e", padx=10, pady=5
            )
            var = tk.StringVar(value="Loading...")
            tk.Label(self.root, textvariable=var, font=("Courier New", 10)).grid(
                row=row_index, column=1, sticky="w", padx=10, pady=5
            )
            self.label_vars[field] = var

        # Script path entry
        self.script_path_var = tk.StringVar(value="run_my_script.py")
        tk.Label(self.root, text="Script Path:", font=("Segoe UI", 10)).grid(
            row=len(self.selected_fields) + 1, column=0, sticky="e", padx=10, pady=10)
        tk.Entry(self.root, textvariable=self.script_path_var, width=40).grid(
            row=len(self.selected_fields) + 1, column=1, sticky="w", padx=10, pady=10)

        # Buttons to run and stop an external script
        ttk.Button(self.root, text="▶ Run Script", command=self.run_external_script).grid(
            row=len(self.selected_fields) + 2, column=0, sticky="e", padx=10, pady=(0, 15))
        self.stop_button = ttk.Button(self.root, text="⏹ Stop Script", command=self.stop_external_script, state="disabled")
        self.stop_button.grid(row=len(self.selected_fields) + 2, column=1, sticky="w", padx=10, pady=(0, 15))

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start periodic telemetry data updates
        self.update_data()
        self.root.mainloop()

    def update_data(self):
        """Pull telemetry data from the client, update GUI fields, optionally print and save to CSV."""
        try:
            data = {}

            # Fetch sensor data only if relevant fields are selected
            if any("GPS" in field for field in self.selected_fields):
                data["gps"] = self.client.getGpsData(gps_name="Gps", vehicle_name="FSCar")
            if any("IMU" in field for field in self.selected_fields):
                data["imu"] = self.client.getImuData(imu_name="Imu", vehicle_name="FSCar")
            if any("LiDAR" in field for field in self.selected_fields):
                data["lidar"] = self.client.getLidarData(lidar_name="Lidar", vehicle_name="FSCar")

            row_values = []
            # Process and display each selected field
            for field in self.selected_fields:
                try:
                    value = self.ALL_POTENTIAL_FIELDS[field](data)
                    self.label_vars[field].set(str(value))
                    row_values.append(value)
                except Exception as e:
                    print(f"Error in field '{field}': {e}")
                    self.label_vars[field].set("Error")
                    row_values.append("Error")

            # Print data to terminal if enabled
            if self.print_to_terminal:
                print(", ".join(f"{field}: {val}" for field, val in zip(self.selected_fields, row_values)))

            # Save data to CSV if enabled
            if self.save_to_csv and self.csv_writer:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.csv_writer.writerow([timestamp] + row_values)
                self.csv_file.flush()  # <--- ADD THIS


        except Exception as e:
            print(f"Connection error: {e}")
            # Display connection error in all fields
            for var in self.label_vars.values():
                var.set("Connection error")

        # Schedule the next update after 1 second
        self.root.after(1000, self.update_data)

    def run_external_script(self):
        """Launch an external Python script specified in the entry box."""
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
        """Stop the external script if running."""
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

    def on_close(self):
        """Cleanup on window close: stop script, close CSV file."""
        if self.csv_file:
            self.csv_file.close()
        if self.script_process:
            self.stop_external_script()
        self.root.destroy()
