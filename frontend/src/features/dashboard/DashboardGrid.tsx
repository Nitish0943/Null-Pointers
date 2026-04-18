"use client";

import React from 'react';
import { useTelemetry } from '@/hooks/useTelemetry';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Activity, ShieldAlert, Cpu, PowerOff, Zap, Play } from 'lucide-react';
import RiskIndicator from '@/components/RiskIndicator';
import ErrorMetrics from '@/components/ErrorMetrics';
import TelemetryGraph from '@/components/TelemetryGraph';

export default function DashboardGrid() {
  const { data, connected, toggleSimulation } = useTelemetry();

  return (
    <div className="flex flex-col gap-6 max-w-[1600px] mx-auto border-transparent">
      
      {/* ─── TOP METRICS ROW ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        
        {/* Connection Status */}
        <Card className="hover:border-primary/20 transition-colors">
          <CardHeader className="flex flex-row justify-between items-center pb-2">
            <CardTitle className="text-[10px]">Machine State</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">
              {data.isSimRunning ? "RUNNING" : "STANDBY"}
            </div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-500 animate-pulse" : "bg-danger"}`} />
              {connected ? "Link Synchronized" : "Connection Lost"}
            </p>
          </CardContent>
        </Card>

        {/* Action Source */}
        <Card className="hover:border-accent/20 transition-colors">
          <CardHeader className="flex flex-row justify-between items-center pb-2">
            <CardTitle className="text-[10px]">Active Stream</CardTitle>
            <HardDriveIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">
              {data.activeSource === 'Standby' ? 'WAITING' : 'ACTIVE'}
            </div>
            <p className="text-xs mt-1">
              {data.activeSource === 'Physical IoT' 
                ? <span className="text-emerald-500 font-bold">Physical IoT Hardware</span> 
                : <span className="text-accent font-bold">Digital Twin Simulation</span>}
            </p>
          </CardContent>
        </Card>

        {/* Global Error */}
        <Card className="hover:border-danger/20 transition-colors">
          <CardHeader className="flex flex-row justify-between items-center pb-2">
            <CardTitle className="text-[10px]">System Error Rate</CardTitle>
            <ShieldAlert className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold font-mono ${((data.posError || 0) + (data.tempError || 0)) > 10 ? 'text-danger' : 'text-foreground'}`}>
              {((data.posError || 0) + (data.tempError || 0)).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Combined positional & thermal drift
            </p>
          </CardContent>
        </Card>

        {/* Control Node */}
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="h-full flex items-center justify-center p-4">
            <Button 
                variant={data.isSimRunning ? "danger" : "primary"}
                size="lg"
                className="w-full gap-2 font-mono h-14"
                onClick={toggleSimulation}
            >
              {data.isSimRunning ? <><PowerOff size={18} /> STOP SIMULATION</> : <><Play size={18} /> START SIMULATION</>}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* ─── MAIN BENTO GRID ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Left Col: Telemetry Charts */}
        <div className="xl:col-span-2 flex flex-col gap-6">
          <Card className="flex-1 overflow-hidden min-h-[300px]">
            <CardHeader className="py-3">
              <CardTitle>Positional Data (mm)</CardTitle>
            </CardHeader>
            <CardContent className="p-0 h-[calc(100%-48px)]">
              <TelemetryGraph title="" data={data.position} color="var(--primary)" unit="mm" />
            </CardContent>
          </Card>
          
          <Card className="flex-1 overflow-hidden min-h-[300px]">
            <CardHeader className="py-3 items-start md:items-center md:flex-row md:justify-between">
              <CardTitle>Thermal Dynamics (°C)</CardTitle>
            </CardHeader>
            <CardContent className="p-0 h-[calc(100%-48px)]">
              <TelemetryGraph title="" data={data.temperature} color="var(--accent)" unit="°C" />
            </CardContent>
          </Card>
        </div>

        {/* Right Col: AI & Risk */}
        <div className="flex flex-col gap-6">
            
            {/* Risk Indicator Panel */}
            <Card className="relative overflow-hidden group min-h-[250px]">
                <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                        Neural Risk Assessment
                        <Badge variant={data.riskScore > 0.6 ? "danger" : (data.riskScore > 0.3 ? "primary" : "success")}>
                           {data.riskScore > 0.6 ? "CRITICAL" : (data.riskScore > 0.3 ? "WARNING" : "STABLE")}
                        </Badge>
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col items-center justify-center flex-1 py-8">
                     <RiskIndicator score={data.riskScore} trend={data.riskTrend} />
                     <div className="w-full mt-6">
                        <ErrorMetrics posError={data.posError} tempError={data.tempError} />
                     </div>
                </CardContent>
            </Card>

            {/* Self-Healing Status Panel */}
            <Card className={`flex-1 flex flex-col min-h-[300px] border-2 transition-all ${data.healing?.issue_detected ? 'border-accent shadow-md glow-accent' : 'border-border'}`}>
                <CardHeader className="pb-4 border-b border-border/50 relative overflow-hidden bg-muted/5">
                    <CardTitle className="flex items-center justify-between z-10 relative">
                        <span className="flex items-center gap-2">
                           <Cpu className={`h-4 w-4 ${data.healing?.issue_detected ? 'text-accent animate-pulse' : 'text-primary'}`} />
                           Self-Healing Engine
                        </span>
                        {data.healing?.issue_detected && data.healing?.verification_status === 'verifying' && (
                           <Badge variant="primary" className="animate-pulse">Active Verification</Badge>
                        )}
                        {data.healing?.verification_status === 'recovered' && (
                           <Badge variant="success">Recovered</Badge>
                        )}
                        {data.healing?.verification_status === 'escalated' && (
                           <Badge variant="danger">Escalated</Badge>
                        )}
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col items-center justify-center p-6 text-center">
                    {!data.healing || !data.healing.issue_detected ? (
                        <>
                           <ShieldAlert size={32} className="mb-4 text-muted-foreground opacity-50" />
                           <p className="font-mono text-sm tracking-widest uppercase text-muted-foreground">System Nominal</p>
                           <p className="text-xs text-muted-foreground/70 mt-2 max-w-xs">Autonomous correction engine is standing by for an anomaly alert.</p>
                        </>
                    ) : (
                        <div className="w-full flex flex-col items-center animate-in fade-in zoom-in duration-300">
                           <p className="text-xs font-bold text-danger uppercase tracking-[0.2em] mb-2 w-full text-left">Threat Neutralized</p>
                           <div className="w-full bg-danger/10 border border-danger/20 rounded-lg p-3 text-left mb-6">
                               <p className="font-mono text-sm text-foreground/90 font-bold">{data.healing.root_cause}</p>
                           </div>
                           
                           <p className="text-xs font-bold text-accent uppercase tracking-[0.2em] mb-2 w-full text-left">Deployed Autonomous Fix</p>
                           <div className="w-full bg-accent/10 border border-accent/20 rounded-lg p-4 text-left relative overflow-hidden">
                               <div className="absolute top-0 right-0 h-full w-1 bg-accent" />
                               <p className="font-mono font-bold text-lg text-accent uppercase">{data.healing.selected_action}</p>
                               {data.healing.action_value !== null && (
                                   <p className="text-sm font-mono text-foreground mt-2">Adjusted Value: <span className="text-accent">{data.healing.action_value}</span></p>
                               )}
                               <p className="text-xs text-muted-foreground mt-2">{data.healing.reasoning}</p>
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
