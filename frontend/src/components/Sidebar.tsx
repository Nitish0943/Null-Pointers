"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Activity, 
  BrainCircuit, 
  Cpu, 
  Settings, 
  ChevronLeft,
  ChevronRight,
  Shield,
  FileText
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (b: boolean) => void;
}

export default function Sidebar({ collapsed, setCollapsed }: SidebarProps) {
  const pathname = usePathname();

  const navGroups = [
    {
      group: "Core",
      items: [
        { name: "Dashboard", href: "/", icon: LayoutDashboard },
        { name: "Telemetry", href: "/telemetry", icon: Activity },
      ]
    },
    {
      group: "Intelligence",
      items: [
        { name: "Digital Twin", href: "/twin", icon: Cpu },
        { name: "AI Insights", href: "/agents", icon: BrainCircuit },
        { name: "Logs", href: "/logs", icon: FileText },
      ]
    },
    {
      group: "System",
      items: [
        { name: "Settings", href: "/settings", icon: Settings },
      ]
    }
  ];

  return (
    <aside className={cn(
      "fixed left-0 top-0 z-40 h-screen transition-all duration-300 ease-in-out border-r border-border glass flex flex-col pt-20",
      collapsed ? "w-[80px]" : "w-[240px]"
    )}>
      <div className="flex-1 overflow-y-auto py-4 px-3 flex flex-col gap-6 custom-scroll">
        {navGroups.map((group, idx) => (
          <div key={idx} className="flex flex-col gap-2">
            {!collapsed && (
              <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/50 px-3 font-tech">
                {group.group}
              </span>
            )}
            {group.items.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all group",
                    isActive 
                      ? "bg-primary/10 text-primary border border-primary/20 glow-primary shadow-sm" 
                      : "text-muted-foreground hover:bg-muted/10 hover:text-foreground border border-transparent"
                  )}
                  title={collapsed ? item.name : undefined}
                >
                  <Icon size={18} className={cn("shrink-0", isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
                  {!collapsed && (
                    <span className="text-xs font-bold uppercase tracking-wider font-tech truncate">
                      {item.name}
                    </span>
                  )}
                </Link>
              )
            })}
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-border/50">
        <button 
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center p-2 rounded-xl text-muted-foreground hover:bg-muted/10 transition-colors border border-transparent hover:border-border/50"
        >
          {collapsed ? <ChevronRight size={18} /> : <div className="flex items-center gap-2 w-full"><ChevronLeft size={18} /><span className="text-xs font-bold uppercase tracking-widest text-muted">Collapse</span></div>}
        </button>
      </div>
    </aside>
  );
}
