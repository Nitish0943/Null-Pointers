"use client";

import React, { useState, useEffect } from 'react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

export default function AppShell({ children }: { children: React.ReactNode }) {
  // Use a layout effect or similar to check screen width if desired,
  // but for now default to false (expanded) on desktop, or true on load to prevent flash.
  const [collapsed, setCollapsed] = useState(false);

  // Auto-collapse on small screens
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setCollapsed(true);
      } else {
        setCollapsed(false);
      }
    };
    handleResize(); // Init
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <>
      <Navbar />
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      <div 
        className="flex-1 flex flex-col h-screen pt-[64px] transition-all duration-300"
        style={{ paddingLeft: collapsed ? '80px' : '240px' }}
      >
        <main className="flex-1 overflow-y-auto custom-scroll p-6">
          {children}
        </main>
      </div>
    </>
  );
}
