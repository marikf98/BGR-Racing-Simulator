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

        launch_button = ttk.Button(self.window, text="▶ Launch Dashboard", command=self.return_values)
        launch_button.pack(pady=20)

        self.window.mainloop()

    def return_values(self):
        self.selected_fields = [field for field, var in self.check_vars.items() if var.get()]
        self.window.destroy()
        return self
        #FSDS_GUI(self.client, self.selected_fields)
