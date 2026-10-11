from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import json, os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "latency.json")
with open(DATA_PATH) as f:
    TELEMETRY = json.load(f)

class AnalyticsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

def compute(req: AnalyticsRequest):
    result = []
    for region in req.regions:
        records = [r for r in TELEMETRY if r["region"] == region]
        if not records:
            continue
        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]
        sorted_lat = sorted(latencies)
        n = len(sorted_lat)
        idx = min(int(0.95 * n), n - 1)
        p95 = sorted_lat[idx]
        result.append({
            "region": region,
            "avg_latency": round(sum(latencies) / len(latencies), 4),
            "p95_latency": round(p95, 4),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 4),
            "breaches": sum(1 for l in latencies if l > req.threshold_ms),
        })
    return result

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}

@app.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(content={}, headers=CORS_HEADERS)

@app.post("/api")
@app.post("/")
@app.post("/check")
async def analyze(req: AnalyticsRequest):
    result = compute(req)
    return JSONResponse(content=result, headers=CORS_HEADERS)
