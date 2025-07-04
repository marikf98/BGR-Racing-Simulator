import sys
import os
import tkinter as tk
from tkinter import ttk
import subprocess

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

        # Extra options
        self.print_to_terminal_var = tk.BooleanVar(value=False)
        self.save_to_csv_var = tk.BooleanVar(value=False)

        print_cb = ttk.Checkbutton(self.window, text="Print selected fields to terminal", variable=self.print_to_terminal_var)
        print_cb.pack(anchor='w', padx=20, pady=(10, 0))

        save_cb = ttk.Checkbutton(self.window, text="Save selected fields to CSV", variable=self.save_to_csv_var)
        save_cb.pack(anchor='w', padx=20)

        # Launch button
        launch_button = ttk.Button(self.window, text="▶ Launch Dashboard", command=self.return_values)
        launch_button.pack(pady=20)

        self.window.mainloop()

    def return_values(self):
        self.selected_fields = [field for field, var in self.check_vars.items() if var.get()]
        self.print_to_terminal = self.print_to_terminal_var.get()
        self.save_to_csv = self.save_to_csv_var.get()

        # Example of what you can do next:
        # You can replace this with a call to your dashboard or pass these values along
        print("Selected fields:", self.selected_fields)
        print("Print to terminal:", self.print_to_terminal)
        print("Save to CSV:", self.save_to_csv)

        self.window.destroy()
        return self  # Optionally return self for further use

# Example usage
if __name__ == "__main__":
    # Replace with your actual client and field list
    dummy_client = None
    fields = ["Speed", "RPM", "Temperature", "GPS", "IMU"]

    selector = FieldSelector(dummy_client, fields)

    # Access selections
    print("Fields selected:", selector.selected_fields)
    print("Print to terminal:", selector.print_to_terminal)
    print("Save to CSV:", selector.save_to_csv)

    # Here you could launch your FSDS_GUI like:
    # FSDS_GUI(selector.client, selector.selected_fields, selector.print_to_terminal, selector.save_to_csv)
