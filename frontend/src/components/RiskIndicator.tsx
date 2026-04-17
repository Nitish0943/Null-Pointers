"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface RiskIndicatorProps {
  score: number; // 0 to 1
  trend?: 'up' | 'down' | 'steady';
}

export default function RiskIndicator({ score, trend = 'steady' }: RiskIndicatorProps) {
  // Color interpolation logic
  const getColor = (val: number) => {
    if (val < 0.3) return 'var(--primary)'; // Normal
    if (val < 0.7) return 'var(--accent)';  // Warning
    return 'var(--danger)';                  // Critical
  };

  const statusText = score < 0.3 ? "SYSTEM NOMINAL" : score < 0.7 ? "DRIFT DETECTED" : "CRITICAL ANOMALY";
  const glowColor = getColor(score);

  return (
    <div className="flex flex-col h-full bg-card border border-border rounded-xl p-6 relative overflow-hidden transition-all duration-300">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">AI Risk Score</h3>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: glowColor }}></div>
          <span className="text-[10px] font-mono font-bold tracking-wider" style={{ color: glowColor }}>{statusText}</span>
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center relative">
        <div className="flex items-end gap-2">
          <div className="text-7xl font-bold font-mono tracking-tighter transition-all" style={{ color: glowColor }}>
            {score.toFixed(2)}
          </div>
          
          {/* Trend Indicator */}
          <div className="flex flex-col items-center pb-2">
            {trend === 'up' ? (
              <div className="flex items-center gap-1 text-danger animate-bounce">
                <TrendingUp size={20} />
                <span className="text-[10px] font-bold">INCREASING</span>
              </div>
            ) : trend === 'down' ? (
              <div className="flex items-center gap-1 text-primary">
                <TrendingDown size={20} />
                <span className="text-[10px] font-bold">DECREASING</span>
              </div>
            ) : (
              <div className="text-muted opacity-50">
                <Minus size={20} />
              </div>
            )}
          </div>
        </div>

        <div className="mt-6 w-full bg-background/50 border border-border rounded-full h-2 overflow-hidden">
          <div 
            className="h-full transition-all duration-700 ease-in-out" 
            style={{ width: `${score * 100}%`, backgroundColor: glowColor }}
          />
        </div>
      </div>
      
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="p-3 bg-background border border-border rounded-lg">
          <div className="text-[10px] text-muted mb-1 uppercase tracking-widest">Stability</div>
          <div className="text-sm font-mono font-bold text-foreground">{(100 - score * 40).toFixed(1)}%</div>
        </div>
        <div className="p-3 bg-background border border-border rounded-lg">
          <div className="text-[10px] text-muted mb-1 uppercase tracking-widest">Confidence</div>
          <div className="text-sm font-mono font-bold text-foreground">94.8%</div>
        </div>
      </div>
    </div>
  );
}

