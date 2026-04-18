"use client";

import { Activity, Thermometer, Hash } from "lucide-react";

interface ErrorMetricsProps {
  posError: number;
  tempError: number;
}

export default function ErrorMetrics({ posError, tempError }: ErrorMetricsProps) {
  return (
    <div className="w-full flex flex-col gap-4">
      <div className="flex items-center gap-2 border-b border-border/50 pb-2 mb-2">
        <Hash size={12} className="text-muted" />
        <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/80 font-tech">Precision Metrics</h3>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-background/40 border border-border/40 rounded-2xl group-hover:border-primary/20 transition-all duration-300">
          <div className="text-[9px] font-black text-muted mb-2 flex items-center gap-2 uppercase tracking-widest">
            <Activity size={10} className="text-primary" /> 
            Latent Position Delta
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-xl font-bold font-mono text-foreground tabular-nums">
              {(posError ?? 0).toFixed(3)}
            </span>
            <span className="text-[9px] font-black text-muted-foreground/40 uppercase">mm</span>
          </div>
        </div>

        <div className="p-4 bg-background/40 border border-border/40 rounded-2xl group-hover:border-accent/20 transition-all duration-300">
          <div className="text-[9px] font-black text-muted mb-2 flex items-center gap-2 uppercase tracking-widest">
            <Thermometer size={10} className="text-accent" /> 
            Thermal Variance
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-xl font-bold font-mono text-foreground tabular-nums">
              {(tempError ?? 0).toFixed(2)}
            </span>
            <span className="text-[9px] font-black text-muted-foreground/40 uppercase">°C</span>
          </div>
        </div>
      </div>
    </div>
  );
}
