"use client";

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useTelemetry } from '@/hooks/useTelemetry';
import { Shield, Wrench, TrendingDown, Activity, History, FastForward } from 'lucide-react';

export default function AdminDashboardPage() {
  const { data } = useTelemetry();

  return (
    <div className="flex flex-col gap-6 max-w-[1600px] mx-auto h-[calc(100vh-100px)]">
      <h1 className="text-2xl font-tech font-bold flex items-center gap-2 shrink-0">
        <Shield className="text-primary" /> Administrator Dashboard
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
        
        {/* Left Column: Maintenance & Severity Analytics */}
        <Card className="flex flex-col h-full">
            <CardHeader className="pb-4">
                <CardTitle className="flex items-center justify-between z-10 relative">
                    <span className="flex items-center gap-2">
                        <Wrench className="h-4 w-4 text-primary" />
                        Maintenance Recovery Center
                    </span>
                    <Badge variant="primary">{data.maintenance.length || 0} Open Tickets</Badge>
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto px-4 custom-scroll space-y-4">
                {!data.maintenance || data.maintenance.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-muted opacity-50 pb-8">
                        <Wrench size={32} className="mb-4" />
                        <span className="text-xs uppercase font-bold tracking-widest text-center">No Active Maintenance Tickets</span>
                    </div>
                ) : (
                    data.maintenance.map(ticket => (
                        <div key={ticket.ticket_id} className="p-4 border border-border/50 rounded-lg flex flex-col gap-3 glow-primary">
                            <div className="flex items-center justify-between">
                                <div className="flex flex-col gap-1">
                                    <span className="font-mono text-xs font-bold text-foreground">{ticket.ticket_id}</span>
                                    <Badge variant={ticket.severity === 'CRITICAL' ? 'danger' : (ticket.severity === 'HIGH' ? 'accent' : 'primary')} className="text-[9px] w-fit">
                                        Severity: {ticket.severity || 'UNKNOWN'}
                                    </Badge>
                                </div>
                                <Badge variant={ticket.priority === 'Critical' ? 'danger' : ticket.priority === 'High' ? 'accent' : 'primary'} className="text-[10px]">
                                    {ticket.priority} Priority
                                </Badge>
                            </div>
                            
                            <div className="text-base font-bold text-accent">{ticket.issue}</div>
                            
                            <div className="text-sm text-foreground/80 grid grid-cols-2 gap-2 bg-muted/20 p-2 rounded-md border border-border/50">
                                <div>
                                    <span className="text-muted-foreground uppercase text-[10px] tracking-widest block">Required Part</span>
                                    <span className="font-mono text-xs">{ticket.recommended_part}</span>
                                </div>
                                <div>
                                    <span className="text-muted-foreground uppercase text-[10px] tracking-widest block">Estimated Time</span>
                                    <span className="font-mono text-xs">{ticket.repair_eta}</span>
                                </div>
                                <div>
                                    <span className="text-muted-foreground uppercase text-[10px] tracking-widest block text-danger">Suggested Loss</span>
                                    <span className="font-mono text-xs text-danger font-bold">₹{ticket.loss_estimate_inr || 0}</span>
                                </div>
                                <div>
                                    <span className="text-muted-foreground uppercase text-[10px] tracking-widest block">Schedule</span>
                                    <span className="font-mono text-xs">{ticket.downtime_window}</span>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </CardContent>
        </Card>

        {/* Right Column: Global Impact Analytics */}
        <div className="flex flex-col gap-6">
            
            {/* Global Production Impact */}
            <Card className="relative overflow-hidden group border-accent/20">
                <CardHeader className="pb-2 bg-accent/5 border-b border-border/50">
                    <CardTitle className="text-xs font-black uppercase tracking-widest flex items-center gap-2">
                        <TrendingDown className="h-3 w-3 text-accent" />
                        Global Production Impact Summary
                    </CardTitle>
                </CardHeader>
                <CardContent className="pt-4 space-y-4">
                    {!data.lossMetrics ? (
                        <div className="py-12 flex flex-col items-center justify-center opacity-30 text-center">
                            <Activity size={32} className="mb-4" />
                            <p className="text-xs uppercase font-bold tracking-widest">Aggregating Global Loss Stream...</p>
                        </div>
                    ) : (
                        <div className="animate-in fade-in slide-in-from-right duration-500">
                             <div className="grid grid-cols-2 gap-4 mb-6">
                                <div className="p-4 bg-muted/20 rounded-xl border border-border/50">
                                    <span className="text-[10px] text-muted-foreground uppercase font-bold block mb-1">Total Units Lost</span>
                                    <div className="text-3xl font-tech font-bold text-accent">{data.lossMetrics.units_lost}</div>
                                </div>
                                <div className="p-4 bg-muted/20 rounded-xl border border-border/50 text-right">
                                    <span className="text-[10px] text-muted-foreground uppercase font-bold block mb-1">Total Revenue Loss</span>
                                    <div className="text-3xl font-tech font-bold text-accent">₹{data.lossMetrics.cost_loss_inr}</div>
                                </div>
                             </div>
                             
                             <div className="p-4 bg-accent/10 rounded-lg border border-accent/20 flex items-center justify-between">
                                <div className="flex flex-col">
                                    <span className="text-[10px] font-bold uppercase text-accent">Urgency Index</span>
                                    <span className="text-lg font-black uppercase tracking-widest text-foreground">{data.lossMetrics.urgency}</span>
                                </div>
                                <div className="text-right flex flex-col items-end">
                                    <span className="text-[10px] font-bold uppercase text-muted-foreground">Recovery Mode</span>
                                    <Badge variant={data.lossMetrics.recovery_priority === 'Immediate' ? 'danger' : 'primary'}>
                                        {data.lossMetrics.recovery_priority}
                                    </Badge>
                                </div>
                             </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* AI Failure Time Machine */}
            <Card className="relative overflow-hidden group border-primary/20 bg-background/50">
                <CardHeader className="pb-2 bg-primary/5 border-b border-border/50">
                    <CardTitle className="text-xs font-black uppercase tracking-widest flex items-center gap-2">
                        <History className="h-3 w-3 text-primary" />
                        AI Failure Time Machine
                    </CardTitle>
                </CardHeader>
                <CardContent className="pt-4 px-0">
                    {!data.failureTimeline ? (
                        <div className="py-10 flex flex-col items-center justify-center opacity-30 text-center">
                            <History size={32} className="mb-4 animate-pulse" />
                            <p className="text-[10px] uppercase font-bold tracking-widest">Awaiting Diagnostic Event...</p>
                        </div>
                    ) : (
                        <div className="animate-in fade-in duration-700">
                             <div className="grid grid-cols-2 divide-x divide-border">
                                {/* Past: Incident Replay */}
                                <div className="px-4 space-y-3">
                                    <div className="flex items-center gap-2 mb-2">
                                        <History className="h-3 w-3 text-muted-foreground" />
                                        <span className="text-[10px] uppercase font-black tracking-widest text-muted-foreground">Incident Replay</span>
                                    </div>
                                    <div className="space-y-2">
                                        {data.failureTimeline.past_events.map((evt, i) => (
                                            <div key={i} className="flex gap-2 items-start group">
                                                <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1 shrink-0 shadow-[0_0_5px_rgba(var(--primary),0.5)]" />
                                                <span className="text-[10px] font-mono leading-tight group-hover:text-primary transition-colors cursor-default">{evt}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Future: Simulation Engine */}
                                <div className="px-4 space-y-3 bg-danger/5">
                                    <div className="flex items-center gap-2 mb-2">
                                        <FastForward className="h-3 w-3 text-danger" />
                                        <span className="text-[10px] uppercase font-black tracking-widest text-danger">Failure Projection</span>
                                    </div>
                                    <div className="space-y-2">
                                        {data.failureTimeline.future_if_ignored.map((evt, i) => (
                                            <div key={i} className="flex gap-2 items-start group">
                                                <div className="h-1.5 w-1.5 rounded-full bg-danger mt-1 shrink-0 shadow-[0_0_5px_rgba(var(--danger),0.5)]" />
                                                <span className="text-[10px] font-mono leading-tight group-hover:text-danger transition-colors cursor-default">{evt}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                             </div>

                             <div className="mt-4 px-4 py-2 bg-muted/30 border-t border-border/50 text-center">
                                <span className="text-[9px] font-tech text-muted-foreground uppercase tracking-[0.2em]">Neural Simulation synchronized with Digital Twin</span>
                             </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* System Log Trace Placeholder */}
            <Card className="flex-1 flex flex-col pointer-events-none opacity-50 bg-muted/5">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-muted-foreground text-xs uppercase tracking-widest">
                        <Shield className="h-3 w-3" /> Administrative System Triage
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col items-center justify-center border-dashed border-2 border-border/20 m-4 rounded-xl">
                   <p className="text-[10px] text-muted-foreground font-mono uppercase tracking-widest">Neural Diagnostic Feed Ready</p>
                </CardContent>
            </Card>
        </div>

      </div>
    </div>
  );
}
