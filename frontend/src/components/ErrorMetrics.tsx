"use client";

import { Activity, Thermometer } from "lucide-react";

interface ErrorMetricsProps {
  posError: number;
  tempError: number;
}

export default function ErrorMetrics({ posError, tempError }: ErrorMetricsProps) {
  return (
    <div className="bg-card border border-border rounded-xl p-4 flex flex-col gap-3">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-2">
        <Activity size={12} /> Deviation Analysis
      </h3>
      
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-background border border-border rounded-lg">
          <div className="text-[10px] text-muted mb-1 flex items-center gap-1 uppercase">
            <Activity size={10} /> Position Error
          </div>
          <div className="text-lg font-mono font-bold text-foreground">
            {posError.toFixed(3)} <span className="text-[10px] font-normal text-muted">mm</span>
          </div>
        </div>

        <div className="p-3 bg-background border border-border rounded-lg">
          <div className="text-[10px] text-muted mb-1 flex items-center gap-1 uppercase">
            <Thermometer size={10} /> Thermal Error
          </div>
          <div className="text-lg font-mono font-bold text-foreground">
            {tempError.toFixed(2)} <span className="text-[10px] font-normal text-muted">°C</span>
          </div>
        </div>
      </div>
    </div>
  );
}
