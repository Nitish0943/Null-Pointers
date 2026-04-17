"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Bell, Info, ShieldAlert, Cpu, Laptop, Terminal, Heart, Wifi, WifiOff } from 'lucide-react';
import TelemetryGraph from './TelemetryGraph';
import RiskIndicator from './RiskIndicator';
import ThemeToggle from './ThemeToggle';
import ErrorMetrics from './ErrorMetrics';

// ─── Types ────────────────────────────────────────────────────────────────────
interface GraphPoint { time: string; actual: number; predicted: number; }
type Trend = 'up' | 'down' | 'steady';

interface DashboardState {
  position: GraphPoint[];
  temperature: GraphPoint[];
  riskScore: number;
  riskTrend: Trend;
  systemMode: string;
  dataSource: string;
  healthStatus: string;
  posError: number;
  tempError: number;
  anomaly: boolean;
  anomalyScore: number;
  alerts: { id: number; type: string; text: string }[];
  recommendations: string[];
}

// ─── Initial seed data (displayed while connecting) ───────────────────────────
function buildSeedData(): DashboardState {
  return {
    position: Array.from({ length: 30 }, (_, i) => ({
      time: `${i}s`,
      actual: 10 + Math.sin(i * 0.4) * 1.5,
      predicted: 10 + Math.sin(i * 0.4) * 1.5,
    })),
    temperature: Array.from({ length: 30 }, (_, i) => ({
      time: `${i}s`,
      actual: 25 + i * 0.3,
      predicted: 25 + i * 0.3,
    })),
    riskScore: 0,
    riskTrend: 'steady',
    systemMode: 'Connecting…',
    dataSource: 'Digital Twin',
    healthStatus: 'Connecting',
    posError: 0,
    tempError: 0,
    anomaly: false,
    anomalyScore: 0,
    alerts: [{ id: 1, type: 'info', text: 'Awaiting live telemetry from backend…' }],
    recommendations: ['Connecting to ws://localhost:8000/ws'],
  };
}

const WS_URL = 'ws://localhost:8000/ws';
const MAX_POINTS = 40;

// ─── Component ────────────────────────────────────────────────────────────────
export default function DashboardContainer() {
  const [mounted, setMounted] = useState(false);
  const [timestamp, setTimestamp] = useState(new Date());
  const [connected, setConnected] = useState(false);
  const [data, setData] = useState<DashboardState>(buildSeedData);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── WebSocket connection manager ────────────────────────────────────────────
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[WS] Connected to backend');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type !== 'TELEMETRY_UPDATE') return;

        const { actual, predicted, analysis } = msg.data;
        const timeLabel = new Date().toLocaleTimeString('en-GB', {
          hour: '2-digit', minute: '2-digit', second: '2-digit',
        });

        setData(prev => {
          // Compute trend
          const newRisk: number = analysis.risk_score ?? 0;
          const trend: Trend =
            newRisk > prev.riskScore + 0.01 ? 'up'
            : newRisk < prev.riskScore - 0.01 ? 'down'
            : 'steady';

          // Health label
          let healthStatus = 'System Stable';
          if (analysis.issue_detected && newRisk > 0.7) healthStatus = 'Critical Anomaly';
          else if (analysis.issue_detected) healthStatus = 'Moderate Drift';
          else if (analysis.anomaly) healthStatus = 'ML Flag';

          // Build alert list from backend recommendation
          const alerts = analysis.issue_detected || analysis.anomaly
            ? [{
                id: Date.now(),
                type: newRisk > 0.7 ? 'critical' : 'warning',
                text: analysis.recommendation ?? 'Anomaly detected',
              }]
            : prev.alerts.length && !prev.alerts[0].text.startsWith('Awaiting')
              ? prev.alerts  // keep last real alert visible
              : [{ id: 1, type: 'info', text: 'All systems nominal.' }];

          return {
            ...prev,
            position: [
              ...prev.position.slice(-(MAX_POINTS - 1)),
              { time: timeLabel, actual: actual.position, predicted: predicted.position },
            ],
            temperature: [
              ...prev.temperature.slice(-(MAX_POINTS - 1)),
              { time: timeLabel, actual: actual.temperature, predicted: predicted.temperature },
            ],
            riskScore: newRisk,
            riskTrend: trend,
            systemMode: 'Live',
            dataSource: 'Backend ML',
            healthStatus,
            posError: Math.abs(actual.position - predicted.position),
            tempError: Math.abs(actual.temperature - predicted.temperature),
            anomaly: analysis.anomaly ?? false,
            anomalyScore: analysis.anomaly_score ?? 0,
            alerts,
            recommendations: [analysis.recommendation ?? 'System Nominal'],
          };
        });
      } catch {
        // Silently ignore malformed frames
      }
    };

    ws.onclose = () => {
      console.log('[WS] Disconnected — retrying in 3s');
      setConnected(false);
      setData(prev => ({
        ...prev,
        systemMode: 'Reconnecting…',
        dataSource: 'Digital Twin',
      }));
      // Auto-reconnect
      reconnectRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  // ── Lifecycle ───────────────────────────────────────────────────────────────
  useEffect(() => {
    setMounted(true);
    const clockTimer = setInterval(() => setTimestamp(new Date()), 1000);

    // Connect to backend WebSocket
    connect();

    return () => {
      clearInterval(clockTimer);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  // ── Helpers ─────────────────────────────────────────────────────────────────
  const connectionDot = connected
    ? 'bg-emerald-500 shadow-[0_0_6px_2px_rgba(16,185,129,0.5)]'
    : 'bg-danger animate-pulse shadow-[0_0_6px_2px_rgba(239,68,68,0.4)]';

  const riskColor =
    data.riskScore > 0.7 ? 'text-danger'
    : data.riskScore > 0.4 ? 'text-accent'
    : 'text-emerald-500';

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-[100dvh] overflow-hidden bg-background text-foreground font-sans p-4 gap-4 transition-colors duration-300">

      {/* ── TOP BAR ─────────────────────────────────────────────────────────── */}
      <header className="flex-none flex items-center justify-between h-14 bg-card border border-border rounded-xl px-6 shadow-sm">

        {/* Left: Logo + Mode badges */}
        <div className="flex items-center gap-5">
          <div className="flex items-center gap-3">
            <div className="bg-primary/20 p-2 rounded-lg border border-primary/30">
              <Cpu size={20} className="text-primary" />
            </div>
            <div>
              <h1 className="text-sm font-black tracking-tight uppercase leading-none">
                Agentic Digital Twin
              </h1>
              <p className="text-[10px] text-muted font-bold tracking-widest mt-0.5">MOTOR-HEATER SUBSYSTEM</p>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-2">
            {/* Connection pill */}
            <div className="flex items-center gap-1.5 py-1 px-3 bg-background border border-border rounded-lg">
              <span className={`w-1.5 h-1.5 rounded-full ${connectionDot}`} />
              {connected
                ? <Wifi size={11} className="text-emerald-500" />
                : <WifiOff size={11} className="text-danger" />}
              <span className="text-[10px] font-bold text-muted uppercase">
                {connected ? 'Live' : 'Offline'}
              </span>
            </div>

            <div className="py-1 px-3 bg-background border border-border rounded-lg flex items-center gap-1.5">
              <Laptop size={11} className="text-muted" />
              <span className="text-[10px] font-bold text-muted uppercase">Mode:</span>
              <span className="text-[10px] font-bold text-primary">{data.systemMode}</span>
            </div>

            <div className="py-1 px-3 bg-background border border-border rounded-lg flex items-center gap-1.5">
              <Terminal size={11} className="text-muted" />
              <span className="text-[10px] font-bold text-muted uppercase">Source:</span>
              <span className="text-[10px] font-bold text-primary">{data.dataSource}</span>
            </div>

            {/* ML Anomaly badge — only show when flagged */}
            {data.anomaly && (
              <div className="py-1 px-3 bg-danger/10 border border-danger/40 rounded-lg flex items-center gap-1.5 animate-pulse">
                <span className="text-[10px] font-black text-danger uppercase tracking-wider">
                  ML ANOMALY  {(data.anomalyScore * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Health + Clock + Toggle */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-background border border-border rounded-lg">
            <Heart size={13} className={`${riskColor} ${data.riskScore > 0.4 ? 'animate-pulse' : ''}`} />
            <span className={`text-[10px] font-black uppercase tracking-widest hidden sm:inline ${riskColor}`}>
              {data.healthStatus}
            </span>
          </div>

          <div className="w-px h-5 bg-border hidden sm:block" />

          <div className="hidden lg:block text-right min-w-[110px]" suppressHydrationWarning>
            {mounted && (
              <>
                <div className="text-[10px] font-mono text-muted tabular-nums">
                  {timestamp.toLocaleDateString('en-GB')}
                </div>
                <div className="text-[10px] font-mono font-bold text-foreground tabular-nums">
                  {timestamp.toLocaleTimeString('en-GB')}
                </div>
              </>
            )}
          </div>

          <ThemeToggle />
        </div>
      </header>

      {/* ── MAIN GRID ───────────────────────────────────────────────────────── */}
      <main className="flex-1 min-h-0 grid grid-cols-10 gap-4 overflow-hidden">

        {/* LEFT: Graphs (60%) */}
        <div className="col-span-6 flex flex-col gap-4 min-h-0">
          <div className="flex-1 min-h-0 relative">
            <TelemetryGraph title="Motor Position Analysis" data={data.position} color="var(--primary)" unit="mm" />
          </div>
          <div className="flex-1 min-h-0 relative">
            <TelemetryGraph title="Core Thermal Telemetry" data={data.temperature} color="var(--accent)" unit="°C" />
          </div>
        </div>

        {/* RIGHT: Panels (40%) */}
        <div className="col-span-4 flex flex-col gap-4 min-h-0">

          {/* Risk Score */}
          <div className="h-[38%] flex-none min-h-0">
            <RiskIndicator score={data.riskScore} trend={data.riskTrend} />
          </div>

          {/* Error Metrics */}
          <div className="flex-none">
            <ErrorMetrics posError={data.posError} tempError={data.tempError} />
          </div>

          {/* Alerts + Recommendations */}
          <div className="flex-1 min-h-0 flex flex-col gap-3 overflow-hidden">

            {/* Alerts */}
            <div className="flex-1 min-h-0 bg-card border border-border rounded-xl p-4 flex flex-col">
              <div className="flex-none flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Bell size={13} className="text-muted" />
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">Active Alerts</h3>
                </div>
                <span className="text-[10px] font-bold text-muted bg-background px-2 py-0.5 rounded border border-border">
                  {data.alerts.length}
                </span>
              </div>
              <div className="flex-1 overflow-y-auto space-y-2 min-h-0 pr-1">
                {data.alerts.map(alert => (
                  <div
                    key={alert.id}
                    className={`flex items-start gap-3 p-2.5 bg-background border rounded-lg transition-all ${
                      alert.type === 'critical' ? 'border-danger/40'
                      : alert.type === 'warning' ? 'border-accent/40'
                      : 'border-border'
                    }`}
                  >
                    <ShieldAlert size={15} className={
                      alert.type === 'critical' ? 'text-danger shrink-0'
                      : alert.type === 'warning' ? 'text-accent shrink-0'
                      : 'text-primary shrink-0'
                    } />
                    <p className="text-[12px] text-foreground/80 leading-snug">{alert.text}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommendations */}
            <div className="flex-1 min-h-0 bg-card border border-border rounded-xl p-4 flex flex-col">
              <div className="flex-none flex items-center gap-2 mb-2">
                <Info size={13} className="text-muted" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">ML Recommendations</h3>
              </div>
              <div className="flex-1 overflow-y-auto min-h-0 pr-1">
                <ul className="space-y-2">
                  {data.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2.5">
                      <div className="mt-2 w-1 h-1 rounded-full bg-primary shrink-0" />
                      <p className="text-[12px] text-muted leading-relaxed">{rec}</p>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}
