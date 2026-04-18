"use client";

import { AlertTriangle, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface RiskIndicatorProps {
  score: number;
  trend: "up" | "down" | "steady";
}

export default function RiskIndicator({ score, trend }: RiskIndicatorProps) {
  const safeScore = score ?? 0;
  const roundedScore = Math.min(1, Math.max(0, safeScore));
  const percentage = (roundedScore * 100).toFixed(1);
  const color = roundedScore > 0.5 ? "var(--danger)" : roundedScore > 0.3 ? "var(--accent)" : "var(--primary)";
  
  // SVG Parameters
  const size = 200;
  const strokeWidth = 12;
  const center = size / 2;
  const radius = center - strokeWidth;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (roundedScore * circumference);

  return (
    <div className="relative flex items-center justify-center group">
      
      {/* Background Glow Ring */}
      <div 
        className="absolute inset-0 rounded-full blur-[40px] opacity-20 transition-all duration-1000 group-hover:opacity-40" 
        style={{ backgroundColor: color }} 
      />

      <svg width={size} height={size} className="transform -rotate-90">
        <defs>
          <filter id="gaugeShadow">
            <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor={color} />
          </filter>
        </defs>

        {/* Outer Background Ring */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="transparent"
          stroke="var(--border)"
          strokeWidth={strokeWidth}
          strokeOpacity={0.1}
        />

        {/* Progress Ring */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="transparent"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          filter="url(#gaugeShadow)"
          className="transition-all duration-1000 ease-out"
        />
      </svg>

      {/* Center Metrics */}
      <div className="absolute inset-0 flex flex-col items-center justify-center select-none">
        <div className="flex flex-col items-center gap-1">
          <span className="text-[10px] font-black uppercase tracking-[0.3em] text-muted-foreground/60 font-tech">Intelligence</span>
          <div className="flex items-baseline gap-1">
            <span className="text-5xl font-bold font-tech tracking-tighter" style={{ color }}>{roundedScore.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 bg-background/50 border border-border rounded-full mt-2 transition-all group-hover:border-primary/20">
            {trend === "up" ? <TrendingUp size={12} className="text-danger" /> : trend === "down" ? <TrendingDown size={12} className="text-emerald-500" /> : <Minus size={12} className="text-muted" />}
            <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground">{trend === "steady" ? "Stable" : trend} Velocity</span>
          </div>
        </div>
      </div>

      {/* Decorative Marks */}
      <div className="absolute inset-0 pointer-events-none opacity-20 group-hover:rotate-45 transition-transform duration-1000">
        {[...Array(8)].map((_, i) => (
          <div 
            key={i} 
            className="absolute w-[1px] h-3 bg-muted" 
            style={{ 
              top: '50%', 
              left: '50%', 
              transform: `translate(-50%, -50%) rotate(${i * 45}deg) translateY(-85px)` 
            }} 
          />
        ))}
      </div>
    </div>
  );
}
