from fastapi import FastAPI
import psutil

app = FastAPI()

# Define a root endpoint to check if the system monitor is running

@app.get("/")
def root():
    return {"status": "System Monitor Running"}

# Define an endpoint to get system metrics such as CPU usage, memory usage, and disk usage

@app.get("/api/metrics")
def get_metrics():
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": dict(psutil.virtual_memory()._asdict()),
        "disk": dict(psutil.disk_usage('/')._asdict()),
    }