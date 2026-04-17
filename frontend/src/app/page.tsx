"use client";

import React, { useState, useEffect } from "react";
import { 
  Activity, 
  Thermometer, 
  Zap, 
  Settings, 
  AlertTriangle, 
  CheckCircle, 
  Cpu,
  BarChart3,
  RefreshCw
} from "lucide-react";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from "recharts";

export default function DigitalTwinDashboard() {
  const [data, setData] = useState<any[]>([]);
  const [latest, setLatest] = useState<any>(null);
  const [status, setStatus] = useState("disconnected");
  const [recs, setRecs] = useState<string[]>([]);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => setStatus("connected");
    ws.onclose = () => setStatus("disconnected");
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "TELEMETRY_UPDATE") {
        const timestamp = new Date().toLocaleTimeString();
        const newData = {
          time: timestamp,
          actualTemp: msg.data.actual.temperature,
          predTemp: msg.data.predicted.temperature,
          actualPos: msg.data.actual.position,
          predPos: msg.data.predicted.position,
          risk: msg.data.analysis.risk_score
        };
        
        setData(prev => [...prev.slice(-19), newData]);
        setLatest(msg.data);
        if (msg.data.analysis.recommendation) {
           setRecs(prev => [msg.data.analysis.recommendation, ...prev.slice(0, 4)]);
        }
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8 font-sans">
      {/* Header */}
      <div className="flex justify-between items-center mb-10">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            Agentic Digital Twin
          </h1>
          <p className="text-slate-400 mt-2 flex items-center gap-2">
            <Cpu size={16} /> Motor–Heater Subsystem Monitor
          </p>
        </div>
        <div className={`px-4 py-2 rounded-full flex items-center gap-2 border ${
          status === "connected" ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-400" : "border-rose-500/50 bg-rose-500/10 text-rose-400"
        }`}>
          <div className={`w-3 h-3 rounded-full animate-pulse ${status === "connected" ? "bg-emerald-500" : "bg-rose-500"}`} />
          {status.toUpperCase()}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
        <StatCard 
          icon={<Thermometer className="text-orange-400" />} 
          label="Actual Temp" 
          value={`${latest?.actual?.temperature?.toFixed(1) || "--"}°C`}
          subValue={`Predicted: ${latest?.predicted?.temperature?.toFixed(1) || "--"}°C`}
        />
        <StatCard 
          icon={<Activity className="text-blue-400" />} 
          label="Actual Position" 
          value={`${latest?.actual?.position?.toFixed(2) || "--"}mm`}
          subValue={`Predicted: ${latest?.predicted?.position?.toFixed(2) || "--"}mm`}
        />
        <StatCard 
          icon={<Zap className="text-yellow-400" />} 
          label="Risk Score" 
          value={`${(latest?.analysis?.risk_score * 100)?.toFixed(0) || "0"}%`}
          subValue={latest?.analysis?.risk_score > 0.5 ? "Insecure State" : "Nominal"}
          isCritical={latest?.analysis?.risk_score > 0.7}
        />
        <StatCard 
          icon={<RefreshCw className="text-cyan-400" />} 
          label="PWM / Steps" 
          value={latest?.actual?.pwm || "0"}
          subValue={`Steps: ${latest?.actual?.steps || 0}`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Charts */}
        <div className="lg:col-span-2 space-y-8">
          <ChartContainer title="Thermal Comparison (Actual vs Twin)">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: "#0f172a", border: "#334155", color: "#f1f5f9" }}
                />
                <Area type="monotone" dataKey="actualTemp" stroke="#f97316" fillOpacity={1} fill="url(#colorTemp)" strokeWidth={2} name="Actual" />
                <Line type="monotone" dataKey="predTemp" stroke="#6366f1" strokeDasharray="5 5" dot={false} name="Predicted (Twin)" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartContainer>

          <ChartContainer title="Motion Tracking (Actual vs Twin)">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip 
                   contentStyle={{ backgroundColor: "#0f172a", border: "#334155", color: "#f1f5f9" }}
                />
                <Line type="monotone" dataKey="actualPos" stroke="#3b82f6" strokeWidth={3} dot={false} name="Actual Position" />
                <Line type="monotone" dataKey="predPos" stroke="#a855f7" strokeDasharray="5 5" dot={false} name="Predicted Position" />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>

        {/* Sidebar / Recommendations */}
        <div className="space-y-8">
          <div className="bg-slate-800/50 border border-slate-700/50 p-6 rounded-2xl">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <BarChart3 className="text-emerald-400" /> AI Agent Terminal
            </h2>
            <div className="space-y-4">
              {recs.length === 0 ? (
                 <div className="text-slate-500 text-sm italic py-4">Waiting for analysis cycle...</div>
              ) : (
                recs.map((r, i) => (
                  <div key={i} className={`p-4 rounded-xl border flex gap-3 transition-all ${
                    r.includes("CRITICAL") ? "bg-rose-500/10 border-rose-500/30 text-rose-200" : "bg-cyan-500/10 border-cyan-500/30 text-cyan-200"
                  }`}>
                    {r.includes("CRITICAL") ? <AlertTriangle size={20} className="shrink-0 text-rose-500" /> : <CheckCircle size={20} className="shrink-0 text-emerald-500" />}
                    <p className="text-sm">{r}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="bg-gradient-to-br from-indigo-600 to-blue-700 p-6 rounded-2xl shadow-xl">
             <h3 className="text-lg font-bold mb-2">System Maintenance</h3>
             <p className="text-indigo-100 text-sm mb-4">The twins are currently within 2.4% tolerance. Next calibration scheduled in 14 hours.</p>
             <button className="w-full py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-sm font-semibold transition-colors">
               Trigger Self-Calibration
             </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, subValue, isCritical = false }: any) {
  return (
    <div className={`p-6 bg-slate-800/50 border rounded-2xl transition-all duration-300 ${
      isCritical ? "border-rose-500/40 bg-rose-500/5 ring-1 ring-rose-500/20" : "border-slate-700/50 hover:border-slate-600"
    }`}>
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-slate-900 rounded-lg">
          {icon}
        </div>
        <span className="text-slate-400 text-sm font-medium">{label}</span>
      </div>
      <div className={`text-3xl font-bold mb-1 ${isCritical ? "text-rose-400" : "text-white"}`}>
        {value}
      </div>
      <div className="text-slate-500 text-xs font-medium">
        {subValue}
      </div>
    </div>
  );
}

function ChartContainer({ children, title }: any) {
  return (
    <div className="bg-slate-800/30 border border-slate-700/50 p-6 rounded-2xl">
      <h3 className="text-lg font-semibold mb-6 text-slate-300">{title}</h3>
      {children}
    </div>
  );
}
