import subprocess
import os
import signal

# This module manages the simulator process
sim_process = None


def launch_simulator():
    global sim_process
    if sim_process is None:
        # Update the path below to match the FSDS.exe location on your system
        sim_path = r""

        if not os.path.exists(sim_path):
            print("❌ Simulator executable not found at:", sim_path)
            return

        print("🚀 Launching FSDS simulator...")
        sim_process = subprocess.Popen([sim_path, os.path.dirname(sim_path)])
    else:
        print("⚠️ Simulator is already running.")
    return

# The function is not working
def stop_simulator():
    global sim_process
    if sim_process is not None:
        print("🛑 Stopping FSDS simulator...")
        try:
            sim_process.terminate()
            sim_process.wait(timeout=10)
        except Exception as e:
            print("⚠️ Failed to terminate normally. Forcing shutdown.")
            os.kill(sim_process.pid, signal.SIGTERM)
        sim_process = None
    else:
        print("ℹ️ Simulator is not running.")
