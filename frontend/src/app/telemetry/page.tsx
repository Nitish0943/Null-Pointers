"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { fetchHistory } from '@/lib/api';
import TelemetryGraph from '@/components/TelemetryGraph';
import { Activity, Database } from 'lucide-react';

export default function TelemetryPage() {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const data = await fetchHistory(50); // Get last 50 points for chart
      // Transform backend data to GraphPoint format for our existing component
      const formatted = data.map((d: any) => ({
        time: new Date(d.timestamp).toLocaleTimeString(),
        actual: d.position,
        predicted: d.predicted_position || d.position, 
        actualTemp: d.temperature,
        predictedTemp: d.predicted_temperature || d.temperature
      })).reverse(); // Oldest first for chart left-to-right

      setHistory(formatted);
      setLoading(false);
    };
    load();
    
    // In a real app we might poll or hook up WebSocket here, but this is a deep dive
    // history page. We'll refresh every 5s for now.
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col gap-6 max-w-[1600px] mx-auto">
      <h1 className="text-2xl font-tech font-bold flex items-center gap-2">
        <Activity className="text-primary" /> Telemetry Archive
      </h1>

      <div className="grid grid-cols-1 gap-6">
        <Card className="min-h-[400px]">
          <CardHeader>
            <CardTitle>Historical Positional Deviation</CardTitle>
          </CardHeader>
          <CardContent className="h-[350px]">
            {loading ? (
              <div className="h-full flex items-center justify-center font-mono text-muted-foreground animate-pulse">
                Fetching archival data...
              </div>
            ) : (
                <TelemetryGraph 
                    title="Position"
                    data={history.map(d => ({ time: d.time, actual: d.actual, predicted: d.predicted }))} 
                    color="var(--primary)" 
                    unit="mm" 
                />
            )}
          </CardContent>
        </Card>

        <Card className="min-h-[400px]">
          <CardHeader>
            <CardTitle>Historical Thermal Dynamics</CardTitle>
          </CardHeader>
          <CardContent className="h-[350px]">
            {loading ? (
              <div className="h-full flex items-center justify-center font-mono text-muted-foreground animate-pulse">
                Fetching archival data...
              </div>
            ) : (
                <TelemetryGraph 
                    title="Temperature"
                    data={history.map(d => ({ time: d.time, actual: d.actualTemp, predicted: d.predictedTemp }))} 
                    color="var(--accent)" 
                    unit="°C" 
                />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
             <CardTitle className="flex items-center gap-2">
                <Database className="h-4 w-4" /> Raw Telemetry Buffer (Last 50)
             </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left border-collapse">
                <thead className="text-xs uppercase bg-muted/20 text-muted-foreground border-b border-border">
                  <tr>
                    <th className="px-4 py-3 font-tech">Timestamp</th>
                    <th className="px-4 py-3 font-tech">Position (mm)</th>
                    <th className="px-4 py-3 font-tech">Temp (°C)</th>
                  </tr>
                </thead>
                <tbody>
                  {[...history].reverse().map((row, idx) => (
                    <tr key={idx} className="border-b border-border/50 hover:bg-muted/10 font-mono">
                      <td className="px-4 py-2 opacity-70">{row.time}</td>
                      <td className="px-4 py-2">{row.actual?.toFixed(2)}</td>
                      <td className="px-4 py-2">{row.actualTemp?.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
