"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { fetchAnalytics, sendAgentMessage } from '@/lib/api';
import { BrainCircuit, Send, MessageSquareText, ShieldAlert } from 'lucide-react';

export default function AgentsPage() {
  const [analytics, setAnalytics] = useState<any>(null);
  const [messages, setMessages] = useState<{role: 'user'|'assistant', content: string}[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const load = async () => setAnalytics(await fetchAnalytics());
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput("");
    setLoading(true);

    const historyForBackend = messages.map(m => ({
      role: m.role === 'assistant' ? 'model' : m.role,
      content: m.content
    }));

    const response = await sendAgentMessage(userMsg, historyForBackend);
    setMessages(prev => [...prev, { role: 'assistant', content: response.response }]);
    setLoading(false);
  };

  const rca = analytics?.rca;

  return (
    <div className="flex flex-col gap-6 max-w-[1600px] mx-auto h-[calc(100vh-100px)]">
      <h1 className="text-2xl font-tech font-bold flex items-center gap-2 shrink-0">
        <BrainCircuit className="text-accent" /> Artificial Intelligence Console
      </h1>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 flex-1 min-h-0">
        
        {/* LEFT COLUMN: RCA Data */}
        <Card className="flex flex-col h-full">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Latest Root Cause Analysis
              <Badge variant={rca?.severity === 'CRITICAL' ? 'danger' : 'primary'}>
                {rca?.severity || 'STANDBY'}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto custom-scroll pr-2">
             {!rca || !rca.root_cause ? (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground font-mono">
                   <ShieldAlert size={32} className="mb-4 opacity-50" />
                   Awaiting structural anomaly detection...
                </div>
             ) : (
                <div className="space-y-6">
                   <div>
                     <h3 className="text-xs uppercase tracking-widest text-muted-foreground font-bold mb-2">Root Cause</h3>
                     <p className="text-sm font-mono p-4 bg-danger/10 border border-danger/20 rounded-md text-danger">
                        {rca.root_cause}
                     </p>
                   </div>
                   
                   <div>
                     <h3 className="text-xs uppercase tracking-widest text-muted-foreground font-bold mb-2">Confidence Score</h3>
                     <div className="flex items-center gap-4">
                        <div className="flex-1 h-2 bg-muted/50 rounded-full overflow-hidden">
                           <div className="h-full bg-accent" style={{ width: `${(rca.confidence_score * 100)}%` }} />
                        </div>
                        <span className="font-mono text-sm">{(rca.confidence_score * 100).toFixed(1)}%</span>
                     </div>
                   </div>

                   <div>
                     <h3 className="text-xs uppercase tracking-widest text-muted-foreground font-bold mb-2">Neural Reasoning</h3>
                     <ul className="list-disc pl-4 space-y-2 text-sm text-foreground/80">
                        {rca.reasoning?.map((r: string, i: number) => (
                           <li key={i}>{r}</li>
                        ))}
                     </ul>
                   </div>

                   <div>
                     <h3 className="text-xs uppercase tracking-widest text-muted-foreground font-bold mb-2">Recommended Action</h3>
                     <p className="text-sm p-4 bg-primary/10 border border-primary/20 rounded-md text-primary font-bold">
                        {rca.recommended_action}
                     </p>
                   </div>
                </div>
             )}
          </CardContent>
        </Card>

        {/* RIGHT COLUMN: Chat Interface */}
        <Card className="flex flex-col h-full">
          <CardHeader className="border-b border-border shadow-sm shrink-0">
             <CardTitle className="flex items-center gap-2">
                <MessageSquareText size={18} className="text-primary" />
                Orchestrator Terminal
             </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col flex-1 p-0 overflow-hidden min-h-0 bg-muted/5">
             
             {/* Chat History */}
             <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scroll">
                {messages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-muted-foreground space-y-2 opacity-50">
                    <BrainCircuit size={48} />
                    <p className="font-mono text-sm max-w-xs text-center mt-4">
                      Direct link established. Ask the orchestrator about the current twin status or to explain anomalies.
                    </p>
                  </div>
                ) : (
                  messages.map((msg, idx) => (
                    <div key={idx} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                       <div className={`max-w-[80%] p-3 rounded-xl text-sm shadow-sm ${
                          msg.role === 'user' 
                          ? 'bg-primary text-primary-foreground rounded-tr-sm' 
                          : 'bg-card border border-border rounded-tl-sm text-foreground/90'
                       }`}>
                          {msg.content}
                       </div>
                    </div>
                  ))
                )}
                {loading && (
                    <div className="flex justify-start">
                       <div className="bg-card border border-border p-3 rounded-xl rounded-tl-sm shadow-sm text-muted-foreground flex items-center gap-2">
                          <span className="animate-bounce">●</span><span className="animate-bounce delay-75">●</span><span className="animate-bounce delay-150">●</span>
                       </div>
                    </div>
                )}
                <div ref={endRef} />
             </div>

             {/* Chat Input */}
             <div className="p-4 bg-card border-t border-border shrink-0">
                <form onSubmit={handleSend} className="flex items-center gap-2">
                   <input 
                      type="text" 
                      value={input}
                      onChange={e => setInput(e.target.value)}
                      placeholder="Query the AI orchestrator..."
                      className="flex-1 bg-background border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary transition-colors font-mono"
                   />
                   <Button type="submit" variant="primary" disabled={loading || !input.trim()}>
                      <Send size={16} />
                   </Button>
                </form>
             </div>

          </CardContent>
        </Card>

      </div>
    </div>
  );
}
