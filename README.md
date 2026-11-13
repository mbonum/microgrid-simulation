# microgrid-sim

Simulation of peer-to-peer energy exchange in a microgrid between **prosumers** (produce + consume) and **consumers** using a bilateral matching algorithm.

## Stack
- **Simulation core**: Python + SimPy + NumPy/Pandas
- **API**: FastAPI + WebSockets
- **Frontend**: React + TypeScript + Recharts

## Quick start

### Backend
```bash
uv venv && source .venv/bin/activate
uv sync
uv run uvicorn api.main:app --reload   # http://localhost:8000
```

### Frontend
```bash
cd frontend
pnpm install
pnpm run dev    # http://localhost:5173
```

### With Docker
```bash
docker compose up
```

### Tests
```bash
pytest          # Python
cd frontend && npm test   # TypeScript
```

## Architecture

```
microgrid-sim/
├── simulation/
│   ├── actors.py      # Prosumer, Consumer, Battery models
│   ├── exchange.py    # Bilateral energy matching
│   ├── grid.py        # SimPy time loop
│   ├── metrics.py     # KPI calculations
│   └── profiles.py    # Synthetic load/solar curves
├── api/
│   └── main.py        # FastAPI + WebSocket endpoints
├── frontend/src/
│   └── App.tsx        # React dashboard
└── tests/
```

## Key concepts

| Term | Meaning |
|------|---------|
| Prosumer | Actor with solar panels — produces AND consumes |
| Consumer | Grid-only consumer |
| Net energy | `production - consumption` (positive = surplus to sell) |
| Clearing price | Midpoint of seller ask / buyer bid when they overlap |
| Self-sufficiency | Share of local demand met without the grid |
