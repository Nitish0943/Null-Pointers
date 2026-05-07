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
  const size = 170;
  const strokeWidth = 10;
  const center = size / 2;
  const radius = center - strokeWidth;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (roundedScore * circumference);

  return (
    <div className="relative flex items-center justify-center group scale-110">
      
      {/* Background Glow Ring */}
      <div 
        className="absolute inset-0 rounded-full blur-[30px] opacity-10 transition-all duration-1000 group-hover:opacity-30" 
        style={{ backgroundColor: color }} 
      />

      <svg width={size} height={size} className="transform -rotate-90">
        <defs>
          <filter id="gaugeShadow">
            <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor={color} />
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
          strokeOpacity={0.08}
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
        <div className="flex flex-col items-center gap-0.5">
          <span className="text-[8px] font-black uppercase tracking-[0.3em] text-muted-foreground/40 font-tech">Intelligence</span>
          <div className="flex items-baseline gap-1">
            <span className="text-4xl font-bold font-tech tracking-tighter" style={{ color }}>{roundedScore.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-1 px-2 py-0.5 bg-background/50 border border-border/50 rounded-full mt-1 transition-all group-hover:border-primary/20">
            {trend === "up" ? <TrendingUp size={10} className="text-danger" /> : trend === "down" ? <TrendingDown size={10} className="text-emerald-500" /> : <Minus size={10} className="text-muted" />}
            <span className="text-[7px] font-black uppercase tracking-[0.2em] text-muted-foreground">{trend === "steady" ? "Stable" : trend} Velocity</span>
          </div>
        </div>
      </div>

      {/* Decorative Marks */}
      <div className="absolute inset-0 pointer-events-none opacity-10 group-hover:rotate-45 transition-transform duration-1000">
        {[...Array(8)].map((_, i) => (
          <div 
            key={i} 
            className="absolute w-[1px] h-2 bg-muted" 
            style={{ 
              top: '50%', 
              left: '50%', 
              transform: `translate(-50%, -50%) rotate(${i * 45}deg) translateY(-72px)` 
            }} 
          />
        ))}
      </div>
    </div>
  );
}
