"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { fetchHistory } from '@/lib/api';
import { FileText, DatabaseZap, Loader2 } from 'lucide-react';

export default function LogsPage() {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterAnomaly, setFilterAnomaly] = useState(false);

  useEffect(() => {
    const load = async () => {
      const data = await fetchHistory(500); // Fetch up to 500 rows for Logs
      setHistory(data);
      setLoading(false);
    };
    load();
  }, []);

  const displayedHistory = filterAnomaly ? history.filter(h => h.anomaly_flag) : history;

  return (
    <div className="flex flex-col gap-6 max-w-[1600px] mx-auto h-[calc(100vh-100px)]">
      <div className="flex items-center justify-between shrink-0">
        <h1 className="text-2xl font-tech font-bold flex items-center gap-2">
          <FileText className="text-primary" /> System Audit Logs
        </h1>
        <div className="flex items-center gap-4 bg-card px-4 py-2 rounded-xl border border-border/50">
          <label className="text-sm font-mono flex items-center gap-2 cursor-pointer select-none">
            <input 
              type="checkbox" 
              checked={filterAnomaly} 
              onChange={e => setFilterAnomaly(e.target.checked)} 
              className="accent-danger w-4 h-4"
            />
            Show Anomalies Only
          </label>
        </div>
      </div>

      <Card className="flex-1 flex flex-col min-h-0">
        <CardHeader className="border-b border-border/50 bg-muted/5 shrink-0">
           <CardTitle className="flex items-center gap-2 text-sm text-muted-foreground">
              <DatabaseZap size={16} /> 
              Latest Database Transactions {displayedHistory.length > 0 && `(${displayedHistory.length} records)`}
           </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-0 custom-scroll relative">
           {loading ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground">
                 <Loader2 size={32} className="animate-spin mb-4" />
                 <span className="font-mono text-sm tracking-widest">Querying Timeseries Database...</span>
              </div>
           ) : displayedHistory.length === 0 ? (
              <div className="absolute inset-0 flex items-center justify-center text-muted-foreground font-mono">
                 No logs match the current criteria.
              </div>
           ) : (
              <table className="w-full text-sm text-left border-collapse">
                <thead className="text-[10px] font-black uppercase tracking-widest bg-muted/20 text-muted-foreground sticky top-0 z-10 shadow-sm">
                  <tr>
                    <th className="px-6 py-4">Timestamp</th>
                    <th className="px-6 py-4">State</th>
                    <th className="px-6 py-4">Pos (mm)</th>
                    <th className="px-6 py-4">Temp (°C)</th>
                    <th className="px-6 py-4">Effort (PWM)</th>
                    <th className="px-6 py-4">ML Score</th>
                  </tr>
                </thead>
                <tbody className="font-mono text-xs">
                  {displayedHistory.map((row, idx) => (
                    <tr key={idx} className="border-b border-border/50 hover:bg-muted/10 transition-colors">
                      <td className="px-6 py-3 whitespace-nowrap text-muted-foreground">
                          {new Date(row.timestamp).toISOString().replace('T', ' ').substring(0, 19)}
                      </td>
                      <td className="px-6 py-3">
                         <Badge variant={row.anomaly_flag ? "danger" : "success"} size="sm">
                            {row.anomaly_flag ? "FAULT" : "OK"}
                         </Badge>
                      </td>
                      <td className="px-6 py-3">
                          <div className="flex flex-col">
                             <span>{Number(row.position).toFixed(2)}</span>
                             <span className="text-[10px] text-muted-foreground border-t border-border mt-1 pt-1 border-dashed">
                                Pred: {Number(row.predicted_position || 0).toFixed(2)}
                             </span>
                          </div>
                      </td>
                      <td className="px-6 py-3">
                          <div className="flex flex-col">
                             <span>{Number(row.temperature).toFixed(2)}</span>
                             <span className="text-[10px] text-muted-foreground border-t border-border mt-1 pt-1 border-dashed">
                                Pred: {Number(row.predicted_temperature || 0).toFixed(2)}
                             </span>
                          </div>
                      </td>
                      <td className="px-6 py-3">
                          {row.pwm}
                      </td>
                      <td className="px-6 py-3">
                          <span className={row.anomaly_score > 0.5 ? "text-danger" : "text-emerald-500"}>
                              {(row.anomaly_score * 100).toFixed(1)}%
                          </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
           )}
        </CardContent>
      </Card>
    </div>
  );
}
