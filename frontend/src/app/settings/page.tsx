"use client";

import React, { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { toggleSimulation } from '@/lib/api';
import { Settings, Moon, Sun, Monitor, Server, Wifi, PowerOff, Play } from 'lucide-react';

export default function SettingsPage() {
  const { theme, setTheme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [isSimRunning, setIsSimRunning] = useState(false);

  // Avoid hydration mismatch
  useEffect(() => setMounted(true), []);

  const handleToggleSim = async () => {
    const res = await toggleSimulation();
    if (res) setIsSimRunning(res.is_running);
  };

  if (!mounted) return null;

  const currentTheme = theme === "system" ? systemTheme : theme;

  return (
    <div className="flex flex-col gap-6 max-w-[1600px] mx-auto pb-10">
      <h1 className="text-2xl font-tech font-bold flex items-center gap-2 shrink-0">
        <Settings className="text-muted-foreground" /> System Configuration
      </h1>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        
        {/* Appearance Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="uppercase tracking-widest text-xs text-muted-foreground">Appearance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <p className="font-bold font-tech mb-4">Interface Theme</p>
              <div className="grid grid-cols-3 gap-4">
                <button 
                  onClick={() => setTheme('light')}
                  className={`flex flex-col items-center justify-center gap-2 p-4 rounded-xl border transition-all ${theme === 'light' ? 'border-primary bg-primary/10 text-primary glow-primary' : 'border-border text-muted-foreground hover:bg-muted/10 hover:border-border/80'}`}
                >
                  <Sun size={24} />
                  <span className="text-xs uppercase font-bold tracking-widest mt-2">Light</span>
                </button>

                <button 
                  onClick={() => setTheme('dark')}
                  className={`flex flex-col items-center justify-center gap-2 p-4 rounded-xl border transition-all ${theme === 'dark' ? 'border-primary bg-primary/10 text-primary glow-primary' : 'border-border text-muted-foreground hover:bg-muted/10 hover:border-border/80'}`}
                >
                  <Moon size={24} />
                  <span className="text-xs uppercase font-bold tracking-widest mt-2">Dark</span>
                </button>

                <button 
                  onClick={() => setTheme('system')}
                  className={`flex flex-col items-center justify-center gap-2 p-4 rounded-xl border transition-all ${theme === 'system' ? 'border-primary bg-primary/10 text-primary glow-primary' : 'border-border text-muted-foreground hover:bg-muted/10 hover:border-border/80'}`}
                >
                  <Monitor size={24} />
                  <span className="text-xs uppercase font-bold tracking-widest mt-2">System</span>
                </button>
              </div>
            </div>
            
            <div className="pt-4 border-t border-border/50">
               <p className="text-sm text-muted-foreground font-mono">
                  Current render node prefers: <span className="text-foreground capitalize">{currentTheme}</span> mode.
               </p>
            </div>
          </CardContent>
        </Card>

        {/* Network & Simulation */}
        <Card>
          <CardHeader>
            <CardTitle className="uppercase tracking-widest text-xs text-muted-foreground">Diagnostics & Control</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            
            <div>
              <p className="font-bold font-tech mb-4 flex items-center gap-2"><Server size={16} /> Connection Endpoints</p>
              <div className="space-y-3 bg-muted/5 p-4 rounded-xl border border-border/50 font-mono text-sm">
                 <div className="flex justify-between items-center pb-3 border-b border-border/50">
                    <span className="text-muted-foreground">REST API Core</span>
                    <span className="text-foreground">http://localhost:8000</span>
                 </div>
                 <div className="flex justify-between items-center pb-3 border-b border-border/50">
                    <span className="text-muted-foreground">WebSocket Telemetry</span>
                    <span className="text-accent">ws://localhost:8000/ws</span>
                 </div>
                 <div className="flex justify-between items-center text-xs text-muted-foreground">
                    <span className="flex items-center gap-1"><Wifi size={12} className="text-emerald-500" /> Linked Local Subnet</span>
                 </div>
              </div>
            </div>

            <div>
              <p className="font-bold font-tech mb-4 flex items-center gap-2"><Play size={16} /> Engine Override</p>
              <div className="bg-muted/5 p-4 rounded-xl border border-border/50">
                 <p className="text-sm text-muted-foreground mb-4 font-mono">
                    Manually engage the backend physical simulation node if hardware ESP32 is offline.
                 </p>
                 <Button 
                    variant={isSimRunning ? "danger" : "primary"}
                    className="w-full gap-2 font-mono h-12"
                    onClick={handleToggleSim}
                 >
                    {isSimRunning ? <><PowerOff size={18} /> HALT SIMULATION ENGINE</> : <><Play size={18} /> ENGAGE SYNTHETIC TWIN</>}
                 </Button>
              </div>
            </div>

          </CardContent>
        </Card>

        {/* Database Stats */}
        <Card className="xl:col-span-2">
          <CardHeader>
             <CardTitle className="uppercase tracking-widest text-xs text-muted-foreground">Local Caching & Storage</CardTitle>
          </CardHeader>
          <CardContent>
             <div className="flex flex-col md:flex-row gap-8 items-center bg-muted/5 p-6 rounded-xl border border-border/50">
                <div className="flex-1">
                   <h3 className="font-bold font-tech mb-2">SQLite Timeseries Edge Database</h3>
                   <p className="text-sm text-muted-foreground max-w-md">
                      The current environment is storing telemetry payloads on the local disk via SQLite. 
                      Cloud synchronization is currently disabled by policy.
                   </p>
                </div>
                <div className="shrink-0 flex items-center gap-4 border-l border-border/50 pl-6 h-full">
                   <div>
                     <p className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground mb-1">Database Mode</p>
                     <p className="font-mono text-emerald-500 font-bold">WRITABLE</p>
                   </div>
                </div>
             </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
