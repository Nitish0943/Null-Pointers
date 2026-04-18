"use client";

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { useTelemetry } from '@/hooks/useTelemetry';
import { BrainCircuit, MessageSquareText, ShieldAlert, Volume2, VolumeX, Mic, Activity, Sparkles } from 'lucide-react';

export default function AgentsPage() {
  const { data } = useTelemetry();
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(false);
  const [displayedText, setDisplayedText] = useState("");
  const typingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Typing Animation Logic
  useEffect(() => {
    if (!data.machineVoice) return;
    
    // Clear previous typing
    if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);
    setDisplayedText("");
    
    let i = 0;
    const text = data.machineVoice;
    
    typingIntervalRef.current = setInterval(() => {
      setDisplayedText(text.substring(0, i + 1));
      i++;
      if (i >= text.length) {
        if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);
      }
    }, 30);

    // Browser TTS Logic
    if (isVoiceEnabled && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.95;
        utterance.pitch = 0.85; // Machine-like deep voice
        window.speechSynthesis.speak(utterance);
    }

    return () => {
      if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);
    };
  }, [data.machineVoice, isVoiceEnabled]);

  const rca = data.riskScore > 0 ? {
    severity: data.riskScore > 0.7 ? 'CRITICAL' : (data.riskScore > 0.3 ? 'HIGH' : 'MEDIUM'),
    root_cause: data.recommendations[0] || 'Analyzing operational deviation...',
    confidence_score: data.riskScore,
    reasoning: data.recommendations.slice(1, 4),
    recommended_action: data.recommendations[0] || 'Standby for diagnostics'
  } : null;

  return (
    <div className="flex flex-col gap-6 max-w-[1600px] mx-auto h-[calc(100vh-100px)]">
      <div className="flex items-center justify-between shrink-0">
        <h1 className="text-2xl font-tech font-bold flex items-center gap-2">
            <BrainCircuit className="text-accent" /> Neural Agent Core
        </h1>
        <Button 
            variant="outline" 
            onClick={() => setIsVoiceEnabled(!isVoiceEnabled)}
            className={`flex items-center gap-2 border-primary/20 ${isVoiceEnabled ? 'bg-primary/10 text-primary' : 'text-muted-foreground'}`}
        >
            {isVoiceEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
            <span className="text-[10px] uppercase font-black tracking-widest">{isVoiceEnabled ? 'Voice Link Active' : 'Enable Voice Link'}</span>
        </Button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 flex-1 min-h-0">
        
        {/* LEFT COLUMN: Data Diagnostics */}
        <Card className="flex flex-col h-full bg-background/50 border-accent/20">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm uppercase tracking-widest font-black">
                <Activity size={16} className="text-accent" />
                Live Diagnostic Context
              </span>
              <Badge variant={rca?.severity === 'CRITICAL' ? 'danger' : 'primary'}>
                {rca?.severity || 'OPERATIONAL'}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto custom-scroll pr-2 space-y-6">
             {!rca ? (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground font-mono opacity-30">
                   <ShieldAlert size={48} className="mb-4" />
                   Awaiting structural anomaly detection...
                </div>
             ) : (
                <div className="space-y-6 animate-in fade-in slide-in-from-left duration-500">
                   <div>
                     <h3 className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold mb-2">Primary Diagnosis</h3>
                     <p className="text-sm font-mono p-4 bg-accent/5 border border-accent/20 rounded-md text-accent glow-text">
                        {rca.root_cause}
                     </p>
                   </div>
                   
                   <div>
                     <h3 className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold mb-2">Neural Link Confidence</h3>
                     <div className="flex items-center gap-4">
                        <div className="flex-1 h-2 bg-muted/50 rounded-full overflow-hidden">
                           <div className="h-full bg-accent shadow-[0_0_10px_rgba(var(--accent),0.5)]" style={{ width: `${(rca.confidence_score * 100)}%` }} />
                        </div>
                        <span className="font-mono text-xs">{(rca.confidence_score * 100).toFixed(1)}%</span>
                     </div>
                   </div>

                   <div>
                     <h3 className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold mb-2">Diagnostic Markers</h3>
                     <div className="space-y-2">
                        {rca.reasoning?.map((r: string, i: number) => (
                           <div key={i} className="flex gap-2 items-center text-xs text-foreground/70 p-2 bg-muted/20 rounded border border-border/50">
                             <div className="h-1 w-1 rounded-full bg-accent" />
                             {r}
                           </div>
                        ))}
                     </div>
                   </div>

                   <div className="pt-4 border-t border-border/50">
                     <h3 className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold mb-2">Strategic Recovery</h3>
                     <p className="text-sm p-4 bg-primary/10 border border-primary/20 rounded-md text-primary font-bold shadow-inner">
                        {rca.recommended_action}
                     </p>
                   </div>
                </div>
             )}
          </CardContent>
        </Card>

        {/* RIGHT COLUMN: Machine Voice Interface */}
        <Card className="flex flex-col h-full bg-card/30 border-primary/20 overflow-hidden relative group">
          <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none" />
          
          <CardHeader className="border-b border-border shadow-sm shrink-0 z-10 bg-background/40 backdrop-blur-md">
             <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm font-black uppercase tracking-[0.2em] text-primary">
                    <Mic size={18} className="animate-pulse" />
                    Machine Voice Output
                </span>
                <Badge variant="outline" className="text-[9px] border-primary/30 text-primary animate-pulse">LIVE NEURAL LINK</Badge>
             </CardTitle>
          </CardHeader>

          <CardContent className="flex flex-col flex-1 p-8 overflow-hidden min-h-0 z-10">
             
             {/* Visual Persona Pulsar */}
             <div className="flex-1 flex flex-col items-center justify-center space-y-8">
                <div className="relative">
                    {/* Concentric pulse rings */}
                    <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping opacity-75" />
                    <div className="absolute inset-0 rounded-full bg-primary/10 animate-ping delay-300 opacity-50" style={{ transform: 'scale(1.5)' }} />
                    <div className="w-24 h-24 rounded-full bg-primary/20 border-2 border-primary/50 flex items-center justify-center relative shadow-[0_0_50px_rgba(var(--primary),0.3)]">
                        <Sparkles className={`w-10 h-10 text-primary ${data.machineVoice ? 'animate-spin-slow' : 'opacity-20'}`} />
                        {data.machineVoice && (
                            <div className="absolute -bottom-2 -right-2">
                                <Badge variant="primary" className="h-6 w-6 rounded-full flex items-center justify-center p-0">
                                    <Activity size={12} />
                                </Badge>
                            </div>
                        )}
                    </div>
                </div>

                <div className="w-full max-w-md text-center space-y-4">
                    {!data.machineVoice ? (
                      <div className="space-y-2 opacity-50">
                        <p className="font-mono text-sm uppercase tracking-widest animate-pulse">Awaiting neural pulse...</p>
                        <p className="text-[10px] text-muted-foreground uppercase px-4">The machine is currently in a state of silent operation</p>
                      </div>
                    ) : (
                      <div className="space-y-6 animate-in zoom-in-95 duration-500">
                        <div className="relative bg-black/40 p-6 rounded-2xl border border-primary/20 shadow-2xl backdrop-blur-sm">
                            <div className="absolute -top-3 left-6">
                                <Badge variant="primary" className="text-[8px] tracking-[0.2em]">DIRECT OUTPUT</Badge>
                            </div>
                            <p className="text-lg md:text-xl font-medium leading-relaxed text-foreground/90 italic">
                                "{displayedText}"
                                <span className="inline-block w-2 h-5 bg-primary ml-1 animate-pulse" />
                            </p>
                        </div>
                        
                        <div className="flex items-center justify-center gap-6">
                            <div className="flex flex-col items-center gap-1">
                                <span className="text-[8px] font-black uppercase text-muted-foreground tracking-tighter">Connection</span>
                                <span className="text-[10px] font-mono text-primary">ENCRYPTED</span>
                            </div>
                            <div className="flex flex-col items-center gap-1">
                                <span className="text-[8px] font-black uppercase text-muted-foreground tracking-tighter">Neural Latency</span>
                                <span className="text-[10px] font-mono text-accent">12ms</span>
                            </div>
                            <div className="flex flex-col items-center gap-1">
                                <span className="text-[8px] font-black uppercase text-muted-foreground tracking-tighter">Vocalize</span>
                                <span className="text-[10px] font-mono text-primary font-bold">{isVoiceEnabled ? 'ACTIVE' : 'MUTED'}</span>
                            </div>
                        </div>
                      </div>
                    )}
                </div>
             </div>

             {/* Footer Status */}
             <div className="mt-auto pt-6 border-t border-border/30 flex items-center justify-between opacity-50">
                <span className="text-[9px] font-mono uppercase tracking-widest flex items-center gap-1">
                    <BrainCircuit size={10} /> Model: Gemini-1.5-Flash
                </span>
                <span className="text-[9px] font-mono uppercase tracking-widest">
                    Telemetry Inhibit: OFF
                </span>
             </div>

          </CardContent>
        </Card>

      </div>
    </div>
  );
}
