from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json, os, statistics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data
DATA_PATH = os.path.join(os.path.dirname(__file__), "latency.json")
with open(DATA_PATH) as f:
    TELEMETRY = json.load(f)

class Request(BaseModel):
    regions: List[str]
    threshold_ms: float

@app.post("/api")
@app.post("/")
@app.post("/check")
def analyze(req: Request):
    result = []
    for region in req.regions:
        records = [r for r in TELEMETRY if r["region"] == region]
        if not records:
            continue
        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]
        sorted_lat = sorted(latencies)
        n = len(sorted_lat)
        idx = int(0.95 * n)
        if idx >= n:
            idx = n - 1
        p95 = sorted_lat[idx]
        result.append({
            "region": region,
            "avg_latency": round(sum(latencies) / len(latencies), 4),
            "p95_latency": round(p95, 4),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 4),
            "breaches": sum(1 for l in latencies if l > req.threshold_ms),
        })
    return result
