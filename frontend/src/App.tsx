import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

const API = "";  // proxied by Vite

type Metrics = {
  self_sufficiency_ratio: number;
  self_consumption_ratio: number;
  total_co2_saved_kg: number;
  peer_traded_kwh: number;
};

type ChartPoint = {
  time: string;
  avg_price: number;
  traded_kwh: number;
  self_sufficiency: number;
};

export default function App() {
  const [running, setRunning] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [finalMetrics, setFinalMetrics] = useState<Metrics | null>(null);

  const [config, setConfig] = useState({
    n_prosumers: 5,
    n_consumers: 5,
    duration_hours: 24,
    grid_fallback_price: 0.30,
    seed: 42,
  });

  async function startSim() {
    setRunning(true);
    setChartData([]);
    setFinalMetrics(null);

    const res = await fetch(`${API}/simulation/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    const { run_id } = await res.json();
    setRunId(run_id);

    // stream via WebSocket
    const ws = new WebSocket(`ws://${location.host}/ws/${run_id}`);
    ws.onmessage = (e) => {
      const snap = JSON.parse(e.data);
      setChartData(prev => [...prev, {
        time: `${snap.time_hours.toFixed(2)}h`,
        avg_price: snap.avg_price,
        traded_kwh: snap.traded_kwh,
        self_sufficiency: snap.metrics.self_sufficiency_ratio,
      }]);
    };
    ws.onclose = async () => {
      const r = await fetch(`${API}/simulation/${run_id}/metrics`);
      const data = await r.json();
      setFinalMetrics(data.final_metrics);
      setRunning(false);
    };
  }

  return (
    <div style={{ fontFamily: "system-ui", maxWidth: 900, margin: "0 auto", padding: 24 }}>
      <h1>⚡ Microgrid Energy Exchange Simulator</h1>

      <section style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 24 }}>
        {(["n_prosumers","n_consumers","duration_hours","seed"] as const).map(k => (
          <label key={k} style={{ display: "flex", flexDirection: "column", fontSize: 13 }}>
            {k.replace(/_/g, " ")}
            <input type="number" value={config[k]}
              onChange={e => setConfig(c => ({ ...c, [k]: Number(e.target.value) }))}
              style={{ width: 80, marginTop: 4 }} />
          </label>
        ))}
        <label style={{ display: "flex", flexDirection: "column", fontSize: 13 }}>
          grid fallback price (€/kWh)
          <input type="number" step="0.01" value={config.grid_fallback_price}
            onChange={e => setConfig(c => ({ ...c, grid_fallback_price: Number(e.target.value) }))}
            style={{ width: 80, marginTop: 4 }} />
        </label>
        <button onClick={startSim} disabled={running}
          style={{ alignSelf: "flex-end", padding: "8px 20px", cursor: running ? "wait" : "pointer" }}>
          {running ? "Running…" : "▶ Run Simulation"}
        </button>
      </section>

      {chartData.length > 0 && (
        <>
          <h3>Average clearing price (€/kWh)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} interval={7} />
              <YAxis domain={[0, 0.35]} tickFormatter={v => `€${v.toFixed(2)}`} />
              <Tooltip formatter={(v: number) => `€${v.toFixed(4)}`} />
              <Line type="monotone" dataKey="avg_price" stroke="#f59e0b" dot={false} />
            </LineChart>
          </ResponsiveContainer>

          <h3>Peer-traded energy per timestep (kWh)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} interval={7} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="traded_kwh" stroke="#10b981" dot={false} />
            </LineChart>
          </ResponsiveContainer>

          <h3>Self-sufficiency ratio</h3>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} interval={7} />
              <YAxis domain={[0, 1]} tickFormatter={v => `${(v*100).toFixed(0)}%`} />
              <Tooltip formatter={(v: number) => `${(v*100).toFixed(1)}%`} />
              <Line type="monotone" dataKey="self_sufficiency" stroke="#6366f1" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </>
      )}

      {finalMetrics && (
        <section style={{ background: "#f0fdf4", border: "1px solid #bbf7d0",
          borderRadius: 8, padding: 16, marginTop: 24 }}>
          <h3 style={{ marginTop: 0 }}>Final KPIs</h3>
          <table><tbody>
            <tr><td>Self-sufficiency</td><td><b>{(finalMetrics.self_sufficiency_ratio*100).toFixed(1)}%</b></td></tr>
            <tr><td>Self-consumption</td><td><b>{(finalMetrics.self_consumption_ratio*100).toFixed(1)}%</b></td></tr>
            <tr><td>Peer-traded</td><td><b>{finalMetrics.peer_traded_kwh.toFixed(2)} kWh</b></td></tr>
            <tr><td>CO₂ saved vs grid</td><td><b>{finalMetrics.total_co2_saved_kg.toFixed(2)} kg</b></td></tr>
          </tbody></table>
        </section>
      )}
    </div>
  );
}
