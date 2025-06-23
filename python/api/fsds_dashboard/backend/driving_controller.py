import subprocess
import os
import sys
def start_autonomous_drive():
    # Step 1: Define the path to the script
    current_dir = os.path.dirname(__file__)  # backend/
    script_path = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "examples", "autonomous_example.py"))

    print(f"🚗 Launching autonomous script at:\n{script_path}")

    # Step 2: Run it using subprocess
    try:
        python_executable = sys.executable  # this points to your active .venv's Python
        subprocess.run([python_executable, script_path], check=True)
        print("✅ Autonomous script finished.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Script crashed: {e}")
    except Exception as e:
        print(f"⚠️ Failed to run script: {e}")
