"use client";

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface DataPoint {
  time: string;
  actual: number;
  predicted: number;
}

interface TelemetryGraphProps {
  title: string;
  data: DataPoint[];
  color: string;
  unit?: string;
}

export default function TelemetryGraph({ title, data, color, unit }: TelemetryGraphProps) {
  return (
    <div className="flex flex-col h-full bg-transparent overflow-hidden p-6 select-none">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-1.5 h-4 rounded-full" style={{ backgroundColor: color }} />
          <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-muted-foreground/70 font-tech">{title}</h3>
        </div>
        <div className="flex items-center gap-2 px-2 py-0.5 rounded bg-background/30 border border-border/50">
          <span className="text-[9px] font-mono text-muted uppercase">Unit: {unit}</span>
        </div>
      </div>
      
      <div className="flex-1 w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id={`gradient-${title.replace(/\s+/g, '')}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.15}/>
                <stop offset="95%" stopColor={color} stopOpacity={0.01}/>
              </linearGradient>
              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>
            
            <CartesianGrid 
              strokeDasharray="4 4" 
              stroke="var(--border)" 
              vertical={false} 
              opacity={0.15}
            />
            
            <XAxis 
              dataKey="time" 
              stroke="var(--muted)" 
              fontSize={9} 
              tickLine={false}
              axisLine={false}
              minTickGap={40}
              dy={10}
              fontFamily="monospace"
            />
            
            <YAxis 
              stroke="var(--muted)" 
              fontSize={9} 
              tickLine={false}
              axisLine={false}
              dx={-5}
              fontFamily="monospace"
              domain={['auto', 'auto']}
            />
            
            <Tooltip
              contentStyle={{ 
                backgroundColor: 'rgba(13, 18, 26, 0.95)', 
                borderColor: 'var(--border)', 
                borderRadius: '16px', 
                fontSize: '11px',
                color: '#fff',
                backdropFilter: 'blur(8px)',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
                border: '1px solid rgba(255,255,255,0.05)'
              }}
              itemStyle={{ color: '#fff', textTransform: 'uppercase', fontScale: '0.8' }}
              cursor={{ stroke: color, strokeWidth: 1, strokeDasharray: '4 4' }}
            />
            
            <Legend 
              iconType="circle" 
              verticalAlign="top"
              align="right"
              wrapperStyle={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.1em', paddingBottom: '20px', fontWeight: 'bold' }} 
            />

            {/* Predicted Line (Subtle) */}
            <Area 
              type="monotone" 
              dataKey="predicted" 
              stroke="var(--muted)" 
              strokeWidth={1}
              strokeDasharray="5 5"
              fill="transparent"
              name="Twin Prediction"
              isAnimationActive={false}
              opacity={0.4}
            />

            {/* Actual Value Line (The Hero) */}
            <Area 
              type="monotone" 
              dataKey="actual" 
              stroke={color} 
              strokeWidth={3}
              fill={`url(#gradient-${title.replace(/\s+/g, '')})`}
              name="Machine Reality"
              isAnimationActive={false}
              filter="url(#glow)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
