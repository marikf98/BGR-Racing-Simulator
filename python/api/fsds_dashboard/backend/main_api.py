print("✅ main_api.py is being loaded.")

from fastapi import FastAPI
from backend.config_generator import generate_settings
from backend.sensor_reader import get_latest_sensor_data
from backend.driving_controller import start_autonomous_drive
from backend.simulator_manager import launch_simulator, stop_simulator

app = FastAPI()

@app.get("/")
def root():
    return {"message": "FSDS Dashboard API is live!"}

@app.post("/config")
def configure(config: dict):
    generate_settings(config)
    return {"message": "Configuration saved to settings.json"}

@app.post("/start-simulator")
def start_sim():
    launch_simulator()
    return {"message": "Simulator launched."}

@app.post("/stop-simulator")
def stop_sim():
    stop_simulator()
    return {"message": "Simulator stopped."}

@app.get("/sensor-data")
def sensor_data():
    data = get_latest_sensor_data()
    return data

@app.post("/drive")
def run_autonomy():
    start_autonomous_drive()
    return {"message": "Autonomous drive started."}




# To run the server: uvicorn backend.main_api:app --reload
# Server adrress: http://localhost:8000/docs#/default/run_autonomy_drive_post