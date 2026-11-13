"""
FastAPI application exposing the microgrid simulation via REST + WebSocket.

Endpoints:
  POST /simulation/start   — start a new sim (returns run_id)
  GET  /simulation/{id}    — fetch full results
  GET  /simulation/{id}/metrics — summary KPIs
  WS   /ws/{id}            — stream live snapshots as simulation runs
"""
from __future__ import annotations
import asyncio
import json
import uuid
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from simulation import run_simulation, SimConfig, SimState
from simulation.metrics import GridMetrics

app = FastAPI(title="Microgrid Simulation API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# in-memory store — swap for Redis/DB in production
_runs: Dict[str, SimState] = {}


class SimRequest(BaseModel):
    n_prosumers: int = 5
    n_consumers: int = 5
    timestep_hours: float = 0.25
    duration_hours: float = 24.0
    grid_fallback_price: float = 0.30
    seed: int = 42


@app.post("/simulation/start")
async def start_simulation(req: SimRequest) -> dict:
    run_id = str(uuid.uuid4())
    cfg = SimConfig(**req.model_dump())

    # Run in thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    state = await loop.run_in_executor(None, run_simulation, cfg)
    _runs[run_id] = state

    return {"run_id": run_id, "n_snapshots": len(state.snapshots)}


@app.get("/simulation/{run_id}")
async def get_simulation(run_id: str) -> dict:
    state = _runs.get(run_id)
    if not state:
        raise HTTPException(404, "Run not found")
    return {
        "run_id": run_id,
        "config": state.config.__dict__,
        "snapshots": [
            {
                "time_hours": s.time_hours,
                "actor_states": s.actor_states,
                "trades": [t.__dict__ for t in s.exchange.trades],
                "unmet_demand_kwh": s.exchange.unmet_demand_kwh,
                "excess_supply_kwh": s.exchange.excess_supply_kwh,
                "avg_price_eur_kwh": s.exchange.avg_price_eur_kwh,
                "metrics": s.metrics.__dict__,
            }
            for s in state.snapshots
        ],
    }


@app.get("/simulation/{run_id}/metrics")
async def get_metrics(run_id: str) -> dict:
    state = _runs.get(run_id)
    if not state:
        raise HTTPException(404, "Run not found")
    last = state.snapshots[-1].metrics if state.snapshots else None
    return {"run_id": run_id, "final_metrics": last.__dict__ if last else {}}


@app.websocket("/ws/{run_id}")
async def ws_stream(websocket: WebSocket, run_id: str) -> None:
    """Stream snapshots one-by-one for a completed run (demo of live feed)."""
    await websocket.accept()
    state = _runs.get(run_id)
    if not state:
        await websocket.close(code=1008)
        return
    try:
        for snap in state.snapshots:
            payload = {
                "time_hours": snap.time_hours,
                "metrics": snap.metrics.__dict__,
                "avg_price": snap.exchange.avg_price_eur_kwh,
                "traded_kwh": snap.exchange.total_volume_kwh,
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.05)  # 50ms between frames
        await websocket.close()
    except WebSocketDisconnect:
        pass
