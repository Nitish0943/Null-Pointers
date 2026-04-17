"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

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
    <div className="flex flex-col h-full bg-card border border-border rounded-xl p-4 overflow-hidden">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">{title}</h3>
        <span className="text-xs text-primary font-mono">LIVE / REAL-TIME</span>
      </div>
      
      <div className="flex-1 w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis 
              dataKey="time" 
              stroke="var(--muted)" 
              fontSize={10} 
              tickLine={false}
              axisLine={false}
              minTickGap={30}
            />
            <YAxis 
              stroke="var(--muted)" 
              fontSize={10} 
              tickLine={false}
              axisLine={false}
              label={unit ? { value: unit, angle: -90, position: 'insideLeft', fill: 'var(--muted)', fontSize: 10 } : undefined}
            />
            <Tooltip
              contentStyle={{ 
                backgroundColor: 'var(--card)', 
                borderColor: 'var(--border)', 
                borderRadius: '8px', 
                fontSize: '12px',
                color: 'var(--foreground)'
              }}
              itemStyle={{ color: 'var(--foreground)' }}
            />
            <Legend 
              iconType="circle" 
              wrapperStyle={{ fontSize: '10px', paddingTop: '10px', color: 'var(--muted)' }} 
            />

            <Line 
              type="monotone" 
              dataKey="actual" 
              stroke={color} 
              strokeWidth={2}
              dot={false}
              name="Actual Value"
              isAnimationActive={false}
            />
            <Line 
              type="monotone" 
              dataKey="predicted" 
              stroke="#64748b" 
              strokeWidth={1.5}
              strokeDasharray="5 5"
              dot={false}
              name="Digital Twin (Predicted)"
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
