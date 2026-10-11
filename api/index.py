import json, os
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

with open(os.path.join(os.path.dirname(__file__), "latency.json")) as f:
    TELEMETRY = json.load(f)

class AnalyticsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

def percentile(values, p):
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)

@app.post("/")
@app.post("/api")
def analyze(req: AnalyticsRequest):
    result = []
    for region in req.regions:
        rows = [r for r in TELEMETRY if str(r["region"]).lower() == region.lower()]
        if not rows:
            continue
        lat = [r["latency_ms"] for r in rows]
        up = [r["uptime_pct"] for r in rows]
        result.append({
            "region": region,
            "avg_latency": round(sum(lat) / len(lat), 4),
            "p95_latency": round(percentile(lat, 95), 4),
            "avg_uptime": round(sum(up) / len(up), 4),
            "breaches": sum(1 for x in lat if x > req.threshold_ms),
        })
    return result
