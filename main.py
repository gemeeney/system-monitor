from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import psutil
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, Session

app = FastAPI()

# ── Database setup ──
engine = create_engine("sqlite:///monitor.db")

class Base(DeclarativeBase):
    pass

class Alert(Base):
    __tablename__ = "alerts"
    id        = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    type      = Column(String)
    message   = Column(String)
    cpu       = Column(Float)
    memory    = Column(Float)
    disk      = Column(Float)

Base.metadata.create_all(engine)

# ── Anomaly detection ──
def check_anomalies(metrics):
    new_alerts = []
    ts  = datetime.fromisoformat(metrics["timestamp"])
    cpu = metrics["cpu"]["percent"]
    mem = metrics["memory"]["percent"]
    dsk = metrics["disk"]["percent"]

    if cpu > 85:
        new_alerts.append(Alert(
            timestamp=ts, type="HIGH_CPU",
            message=f"CPU spike: {cpu}%",
            cpu=cpu, memory=mem, disk=dsk
        ))
    if mem > 90:
        new_alerts.append(Alert(
            timestamp=ts, type="HIGH_MEMORY",
            message=f"Memory critical: {mem}%",
            cpu=cpu, memory=mem, disk=dsk
        ))
    if dsk > 90:
        new_alerts.append(Alert(
            timestamp=ts, type="HIGH_DISK",
            message=f"Disk critical: {dsk}%",
            cpu=cpu, memory=mem, disk=dsk
        ))
    return new_alerts

# ── Routes ──
@app.get("/api/metrics")
def get_metrics():
    cpu  = psutil.cpu_percent(interval=1)
    mem  = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net  = psutil.net_io_counters()

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "cpu": {"percent": cpu},
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb":  round(mem.used  / (1024**3), 2),
            "percent":  mem.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb":  round(disk.used  / (1024**3), 2),
            "percent":  disk.percent
        },
        "network": {
            "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2)
        }
    }

    new_alerts = check_anomalies(metrics)
    if new_alerts:
        with Session(engine) as session:
            session.add_all(new_alerts)
            session.commit()

    return metrics

@app.get("/api/alerts")
def get_alerts():
    with Session(engine) as session:
        rows = session.query(Alert).order_by(Alert.id.desc()).limit(20).all()
        return {
            "total": session.query(Alert).count(),
            "alerts": [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "type":      r.type,
                    "message":   r.message,
                    "cpu":       r.cpu,
                    "memory":    r.memory,
                    "disk":      r.disk
                }
                for r in rows
            ]
        }

app.mount("/", StaticFiles(directory="static", html=True), name="static")