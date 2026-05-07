"use client";

import React, { useState } from 'react';
import { useTelemetry } from '@/hooks/useTelemetry';
import { setSimulationPosition, setSimulationTemperature } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Activity, ShieldAlert, Cpu, PowerOff, Play } from 'lucide-react';
import RiskIndicator from '@/components/RiskIndicator';
import ErrorMetrics from '@/components/ErrorMetrics';
import TelemetryGraph from '@/components/TelemetryGraph';

export default function DashboardGrid() {
  const { data, connected, toggleSimulation } = useTelemetry();
  const [targetPos, setTargetPos] = useState<string>('');
  const [targetTemp, setTargetTemp] = useState<string>('');

  const handleExecutePos = async () => {
    if (!targetPos) return;
    try {
      await setSimulationPosition(parseFloat(targetPos));
      setTargetPos('');
    } catch (e) {
      console.error("Failed to set position", e);
    }
  };

  const handleExecuteTemp = async () => {
    if (!targetTemp) return;
    try {
      await setSimulationTemperature(parseFloat(targetTemp));
      setTargetTemp('');
    } catch (e) {
      console.error("Failed to set temperature", e);
    }
  };

  return (
    <div className="flex flex-col gap-4 max-w-[1600px] mx-auto h-[calc(100vh-120px)] overflow-hidden px-4">
      
      {/* ─── TOP METRICS ROW ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 shrink-0 px-2 lg:px-0">
        
        {/* Connection Status */}
        <Card className="hover:border-primary/20 transition-colors py-1.5 px-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/60">Machine State</span>
            <Activity className="h-3 w-3 text-muted-foreground/40" />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-lg font-bold font-mono tracking-tight">{data.isSimRunning ? "RUNNING" : "STANDBY"}</span>
            <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-emerald-500 animate-pulse shadow-[0_0_8px_var(--emerald-500)]" : "bg-danger"}`} />
          </div>
          <p className="text-[8px] text-muted-foreground/80 mt-0.5 font-mono uppercase tracking-tighter">
            {connected ? "NEURAL LINK ACTIVE" : "LINK SEVERED"}
          </p>
        </Card>

        {/* Action Source */}
        <Card className="hover:border-accent/20 transition-colors py-1.5 px-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/60">Active Stream</span>
            <HardDriveIcon className="h-3 w-3 text-muted-foreground/40" />
          </div>
          <div className="text-lg font-bold font-mono">
            {data.activeSource === 'Standby' ? 'WAITING' : 'ACTIVE'}
          </div>
          <p className="text-[9px] mt-0.5 font-bold uppercase tracking-tighter">
            {data.activeSource === 'Physical IoT' 
              ? <span className="text-emerald-500">Physical Hardware</span> 
              : <span className="text-accent">Digital Twin</span>}
          </p>
        </Card>

        {/* Global Error */}
        <Card className="hover:border-danger/20 transition-colors py-1.5 px-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/60">System Error</span>
            <ShieldAlert className="h-3 w-3 text-muted-foreground/40" />
          </div>
          <div className={`text-lg font-bold font-mono ${((data.posError || 0) + (data.tempError || 0)) > 10 ? 'text-danger' : 'text-foreground'}`}>
            {((data.posError || 0) + (data.tempError || 0)).toFixed(1)}%
          </div>
          <p className="text-[8px] text-muted-foreground mt-0.5 uppercase tracking-tighter">
            Combined Drift Metrics
          </p>
        </Card>

        {/* Control Node */}
        <Card className="bg-primary/5 border-primary/20 overflow-hidden relative group">
           <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
           <CardContent className="h-full flex items-center justify-center p-2 relative z-10">
            <Button 
                variant={data.isSimRunning ? "danger" : "primary"}
                size="sm"
                className="w-full gap-2 font-black h-10 text-[10px] tracking-[0.2em] shadow-lg transition-all active:scale-95"
                onClick={toggleSimulation}
            >
              {data.isSimRunning ? <><PowerOff size={14} /> STOP</> : <><Play size={14} /> START SYSTEM</>}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* ─── MAIN BENTO GRID (Viewport Optimized) ────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 flex-1 min-h-0 min-w-0 overflow-hidden">
        
        {/* Left Col: Telemetry Charts (Swapped Order) */}
        <div className="xl:col-span-2 flex flex-col gap-4 min-h-0 min-w-0">
          
          {/* Thermal Dynamics (NOW ON TOP) */}
          <Card className="flex-1 overflow-hidden min-h-0 min-w-0 flex flex-col">
            <CardHeader className="py-2 flex flex-row items-center justify-between shrink-0">
              <CardTitle className="text-sm">Thermal Dynamics (°C)</CardTitle>
              <div className="flex items-center gap-2">
                <input 
                  type="number" 
                  step="0.1"
                  placeholder="Target °C..."
                  value={targetTemp}
                  onChange={(e) => setTargetTemp(e.target.value)}
                  className="w-20 h-7 bg-muted/20 border border-border/50 rounded px-2 text-[10px] font-mono focus:outline-none focus:border-accent/50"
                />
                <Button 
                  size="sm" 
                  variant="secondary"
                  className="h-7 px-2 text-[8px] font-tech tracking-wider border-accent/20 hover:border-accent/50"
                  onClick={handleExecuteTemp}
                  disabled={!targetTemp}
                >
                  EXECUTE
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0 flex-1 min-h-0 min-w-0">
              <TelemetryGraph title="" data={data.temperature} color="var(--accent)" unit="°C" />
            </CardContent>
          </Card>

          {/* Positional Data (NOW BELOW) */}
          <Card className="flex-1 overflow-hidden min-h-0 min-w-0 flex flex-col">
            <CardHeader className="py-2 flex flex-row items-center justify-between shrink-0">
              <CardTitle className="text-sm">Positional Data (mm)</CardTitle>
              <div className="flex items-center gap-2">
                <input 
                  type="number" 
                  step="0.01"
                  placeholder="Target mm..."
                  value={targetPos}
                  onChange={(e) => setTargetPos(e.target.value)}
                  className="w-20 h-7 bg-muted/20 border border-border/50 rounded px-2 text-[10px] font-mono focus:outline-none focus:border-primary/50"
                />
                <Button 
                  size="sm" 
                  className="h-7 px-2 text-[8px] font-tech tracking-wider"
                  onClick={handleExecutePos}
                  disabled={!targetPos}
                >
                  EXECUTE
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0 flex-1 min-h-0 min-w-0">
              <TelemetryGraph title="" data={data.position} color="var(--primary)" unit="mm" />
            </CardContent>
          </Card>
        </div>

        {/* Right Col: AI & Risk */}
        <div className="flex flex-col gap-4 min-h-0">
            
            {/* Risk Indicator Panel */}
            <Card className="relative overflow-hidden group h-[55%] flex flex-col shrink-0">
                  <CardHeader className="py-2 shrink-0 border-b border-border/50 bg-muted/5">
                    <CardTitle className="flex items-center justify-between text-[11px] font-black tracking-widest uppercase text-muted-foreground/80">
                        Neural Risk Assessment
                        <Badge variant={data.riskScore > 0.6 ? "danger" : (data.riskScore > 0.3 ? "primary" : "success")} className="text-[8px] py-0 px-1 font-mono">
                           {(data.riskScore * 100).toFixed(1)}% {data.riskScore > 0.6 ? "CRITICAL" : (data.riskScore > 0.3 ? "WARNING" : "STABLE")}
                        </Badge>
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col items-center justify-center flex-1 min-h-0 pb-4 pt-2">
                     <div className="scale-[0.8] origin-center -my-2 flex-1 flex items-center justify-center">
                        <RiskIndicator score={data.riskScore} trend={data.riskTrend} />
                     </div>
                     <div className="w-full px-3 shrink-0">
                        <ErrorMetrics posError={data.posError} tempError={data.tempError} />
                     </div>
                </CardContent>
            </Card>

            {/* Self-Healing Engine Panel */}
            <Card className={`flex-1 flex flex-col min-h-0 border transition-all ${data.healing?.issue_detected ? 'border-accent/40 shadow-lg shadow-accent/10' : 'border-border'}`}>
                <CardHeader className="py-2 border-b border-border/50 bg-muted/5 shrink-0">
                    <CardTitle className="flex items-center justify-between text-[11px] font-black tracking-widest uppercase text-muted-foreground/80">
                        <span className="flex items-center gap-2">
                           <Cpu className={`h-3 w-3 ${data.healing?.issue_detected ? 'text-accent animate-pulse' : 'text-primary'}`} />
                           Self-Healing Engine
                        </span>
                        {data.healing?.issue_detected && <Badge variant="primary" className="animate-pulse text-[8px] py-0 px-2">ACTIVE CORRECTION</Badge>}
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col items-center justify-center p-4 text-center min-h-0">
                    {!data.healing || !data.healing.issue_detected ? (
                        <div className="animate-in fade-in duration-700">
                           <ShieldAlert size={20} className="mb-2 text-muted-foreground/30 mx-auto" />
                           <p className="font-mono text-[9px] tracking-[0.2em] uppercase text-muted-foreground/60 leading-tight">Autonomous Guard Standing By</p>
                        </div>
                    ) : (
                        <div className="w-full flex flex-col items-center animate-in slide-in-from-bottom-2 duration-500">
                           <div className="w-full text-left">
                               <span className="text-[8px] font-black text-danger/50 uppercase tracking-[0.2em]">Threat Log</span>
                               <p className="font-mono text-[10px] text-foreground/90 font-bold bg-danger/5 border border-danger/20 p-2 rounded mt-1 mb-3 leading-tight">{data.healing.root_cause}</p>
                           </div>
                           
                           <div className="w-full text-left">
                               <span className="text-[8px] font-black text-accent/50 uppercase tracking-[0.2em]">Deployed Strategy</span>
                               <div className="bg-accent/5 border border-accent/20 rounded p-2 mt-1 relative overflow-hidden group/fix">
                                   <div className="absolute left-0 top-0 bottom-0 w-1 bg-accent/30 group-hover/fix:bg-accent transition-colors" />
                                   <p className="font-mono font-black text-xs text-accent uppercase">{data.healing.selected_action}</p>
                                   <p className="text-[9px] text-muted-foreground mt-1 leading-snug line-clamp-2 italic">{data.healing.reasoning}</p>
                               </div>
                           </div>
                        </div>
                    )}
                </CardContent>
            </Card>

        </div>
      </div>
    </div>
  );
}

function HardDriveIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="22" x2="2" y1="12" y2="12" />
      <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
      <line x1="6" x2="6.01" y1="16" y2="16" />
      <line x1="10" x2="10.01" y1="16" y2="16" />
    </svg>
  )
}
