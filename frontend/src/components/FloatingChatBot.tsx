"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { MessageSquare, X, Send, BrainCircuit, Activity, ShieldCircle, Zap } from 'lucide-react';
import { sendAgentMessage } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function FloatingChatBot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "Neural Link Established. I am the Fluidd Core. How can I assist with our operation today?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      endRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: 'user', content: userText }]);
    setLoading(true);

    try {
      const historyForBackend = messages.map(m => ({
        role: m.role === 'assistant' ? 'model' : m.role,
        content: m.content
      }));

      const res = await sendAgentMessage(userText, historyForBackend);
      setMessages(prev => [...prev, { role: 'assistant', content: res.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Communication failure. My neural engine responded with an error." }]);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    { label: "Status Check", query: "What is your current health status?" },
    { label: "Check Risk", query: "Are there any immediate risks I should know about?" },
    { label: "Maintenance", query: "What is my next recommended maintenance action?" }
  ];

  return (
    <div className="fixed bottom-6 right-6 z-[9999]">
      {!isOpen ? (
        <button
          onClick={() => setIsOpen(true)}
          className="group relative h-14 w-14 rounded-full bg-primary text-primary-foreground shadow-[0_0_20px_rgba(var(--primary),0.4)] flex items-center justify-center transition-all hover:scale-110 active:scale-95"
        >
          <div className="absolute inset-0 rounded-full border-2 border-primary animate-ping opacity-20" />
          <BrainCircuit className="h-6 w-6 group-hover:rotate-12 transition-transform" />
        </button>
      ) : (
        <Card className="w-[380px] h-[520px] shadow-2xl border-primary/20 flex flex-col overflow-hidden animate-in slide-in-from-bottom-4 duration-300">
          <CardHeader className="py-3 px-4 bg-primary/10 border-b border-border flex flex-row items-center justify-between shrink-0">
            <CardTitle className="text-xs font-black uppercase tracking-widest flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-primary animate-pulse shadow-[0_0_5px_rgba(var(--primary),1)]" />
              Fluidd Neural Core
            </CardTitle>
            <button onClick={() => setIsOpen(false)} className="text-muted-foreground hover:text-foreground">
              <X size={16} />
            </button>
          </CardHeader>
          
          <CardContent className="flex-1 flex flex-col p-0 overflow-hidden min-h-0">
            {/* Message History */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scroll bg-muted/5 font-tech">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] px-3 py-2 rounded-xl text-xs ${
                    msg.role === 'user' 
                    ? 'bg-primary text-primary-foreground rounded-tr-none'
                    : 'bg-card border border-border rounded-tl-none shadow-sm'
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-card border border-border px-3 py-2 rounded-xl rounded-tl-none text-[8px] flex items-center gap-1 opacity-50">
                    <Zap size={10} className="animate-spin text-primary" />
                    DECODING NEURAL PULSE...
                  </div>
                </div>
              )}
              <div ref={endRef} />
            </div>

            {/* Quick Actions */}
            <div className="px-4 py-2 flex gap-2 overflow-x-auto no-scrollbar border-t border-border/50 bg-background/50">
                {quickActions.map((action, i) => (
                    <button
                        key={i}
                        onClick={() => { setInput(action.query); }}
                        className="whitespace-nowrap px-2 py-1 rounded-full border border-primary/20 text-[9px] uppercase font-bold text-muted-foreground hover:border-primary hover:text-primary transition-colors"
                    >
                        {action.label}
                    </button>
                ))}
            </div>

            {/* Input Area */}
            <div className="p-3 border-t border-border bg-card">
              <form onSubmit={handleSend} className="flex gap-2">
                <input
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder="Ask the Twin..."
                  className="flex-1 bg-background border border-border rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-primary transition-colors"
                />
                <Button type="submit" size="sm" disabled={loading || !input.trim()} className="shrink-0 h-8 w-8 p-0 rounded-full">
                  <Send size={14} />
                </Button>
              </form>
              <div className="mt-2 text-center">
                <span className="text-[8px] uppercase tracking-tighter text-muted-foreground opacity-50">Secure Neural Link Est. 12ms</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
