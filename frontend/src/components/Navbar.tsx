"use client";

import Link from "next/link";
import { Shield, Activity, HardDrive } from "lucide-react";
import ThemeToggle from "./ThemeToggle";
import { cn } from "@/utils/cn";

export default function Navbar() {
  // In a real implementation, this would be fed by a global context or hook.
  // For now, it represents the ideal UI state layout.
  const isConnected = true;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 h-[64px] border-b border-border glass bg-background/80 px-6 flex items-center justify-between">
      
      {/* Brand & Left Side */}
      <div className="flex items-center gap-6 w-[240px]">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground shadow-lg shadow-primary/20">
            <Shield size={16} className="group-hover:rotate-12 transition-transform" />
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-bold tracking-tight uppercase font-tech leading-none mb-0.5">Fluidd Twin</span>
            <span className="text-[8px] font-black uppercase tracking-[0.2em] text-muted-foreground leading-none">OS v9.2.0</span>
          </div>
        </Link>
      </div>

      {/* Center - Machine Status */}
      <div className="hidden md:flex items-center gap-4">
        <div className="flex items-center gap-3 px-4 py-1.5 rounded-full border border-border bg-background/50">
          <HardDrive size={14} className="text-muted" />
          <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Machine State: </span>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[10px] font-mono font-bold text-emerald-500 tracking-wider">SECURE & RUNNING</span>
          </div>
        </div>
      </div>

      {/* Right Side - System & Theme */}
      <div className="flex items-center gap-6">
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-background/50">
          <Activity size={12} className={cn("transition-colors", isConnected ? "text-primary animate-heartbeat" : "text-danger")} />
          <span className="text-[9px] font-mono text-muted uppercase">Latency: <span className="text-primary font-bold">12ms</span></span>
        </div>

        <ThemeToggle />
      </div>
    </div>
  );
}
