import { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE = "http://localhost:8000";
const WS_BASE = "ws://localhost:8000/ws";

interface GraphPoint { time: string; actual: number; predicted: number; }
type Trend = 'up' | 'down' | 'steady';

export interface TelemetryState {
  position: GraphPoint[];
  temperature: GraphPoint[];
  riskScore: number;
  riskTrend: Trend;
  posError: number;
  tempError: number;
  alerts: { id: number; type: string; text: string }[];
  recommendations: string[];
  isSimRunning: boolean;
  activeSource: string;
  healing: any | null;
}

export function useTelemetry() {
  const [data, setData] = useState<TelemetryState>({
    position: [],
    temperature: [],
    riskScore: 0,
    riskTrend: 'steady',
    posError: 0,
    tempError: 0,
    alerts: [],
    recommendations: ["System initializing...", "Establishing Neural Link..."],
    isSimRunning: false,
    activeSource: 'Standby',
    healing: null
  });

  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const toggleSimulation = async () => {
    try {
      const resp = await fetch(`${API_BASE}/simulation/toggle`, { method: 'POST' });
      if (resp.ok) {
        const result = await resp.json();
        setData(prev => ({ ...prev, isSimRunning: result.is_running }));
      }
    } catch (e) {
      console.error("Transmission Failure", e);
    }
  };

  useEffect(() => {
    let cleanup = false;
    let retryTimeout: NodeJS.Timeout;

    const connect = () => {
      if (cleanup) return;
      
      const ws = new WebSocket(WS_BASE);
      wsRef.current = ws;

      ws.onopen = () => {
        if (cleanup) return;
        setConnected(true);
      };

      ws.onmessage = (event) => {
        if (cleanup) return;
        const msg = JSON.parse(event.data);

        switch (msg.type) {
          case 'TELEMETRY_UPDATE':
            const timeStr = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
            setData(prev => ({
              ...prev,
              position: [...prev.position.slice(-29), { 
                time: timeStr, 
                actual: msg.data.actual.position, 
                predicted: msg.data.predicted.position 
              }],
              temperature: [...prev.temperature.slice(-29), { 
                time: timeStr, 
                actual: msg.data.actual.temperature, 
                predicted: msg.data.predicted.temperature 
              }],
              riskScore: msg.data.analysis.risk_score,
              posError: msg.data.analysis.position_error,
              tempError: msg.data.analysis.temperature_error,
              activeSource: msg.data.actual.source === 'iot' ? 'Physical IoT' : 'Simulation',
              healing: msg.data.analysis.agents?.healing || null
            }));
            break;

          case 'MONITORING_ALERT':
            setData(prev => ({ 
              ...prev, 
              alerts: [ { id: Date.now(), type: msg.severity, text: msg.message }, ...prev.alerts.slice(0, 9) ] 
            }));
            break;

          case 'RCA_UPDATE':
            setData(prev => ({ 
              ...prev, 
              recommendations: [ msg.explanation, ...msg.recommendations ] 
            }));
            break;

          case 'SIM_STATUS':
            setData(prev => ({ ...prev, isSimRunning: msg.is_running }));
            break;
        }
      };

      ws.onclose = () => {
        if (cleanup) return;
        setConnected(false);
        retryTimeout = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      cleanup = true;
      clearTimeout(retryTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return { data, connected, toggleSimulation };
}
