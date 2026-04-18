"use client";

import { useState, useRef, useEffect } from "react";
import { 
  MessageSquare, 
  X, 
  Send, 
  Bot, 
  User, 
  Loader2, 
  Minimize2, 
  Sparkles,
  Info
} from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm your Digital Twin Expert. I have real-time access to the machine's telemetry and health metrics. How can I help you today?",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isOpen]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const resp = await fetch("http://localhost:8000/agents/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: input,
          history: messages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      if (resp.ok) {
        const data = await resp.json();
        const assistantMsg: Message = {
          role: "assistant",
          content: data.response,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } else {
        throw new Error("Failed to fetch response");
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "I'm sorry, I'm having trouble connecting to the machine's neural engine. Please verify the backend is running.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 right-6 z-[60] p-4 rounded-2xl shadow-2xl transition-all duration-500 group ${
          isOpen 
          ? "bg-destructive text-destructive-foreground rotate-90" 
          : "bg-primary text-primary-foreground hover:scale-110 active:scale-95 shadow-primary/40 hover:shadow-primary/60"
        }`}
      >
        {isOpen ? <X size={24} /> : (
          <div className="relative">
            <MessageSquare size={24} />
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full border-2 border-primary animate-pulse" />
          </div>
        )}
      </button>

      {/* Chat Window */}
      <div
        className={`fixed bottom-24 right-6 z-[60] w-[400px] h-[600px] max-h-[80vh] bg-card border border-border rounded-[32px] shadow-2xl transition-all duration-500 flex flex-col overflow-hidden ${
          isOpen ? "translate-y-0 opacity-100 scale-100" : "translate-y-12 opacity-0 scale-95 pointer-events-none"
        }`}
      >
        {/* Header */}
        <div className="p-6 border-b border-border bg-gradient-to-r from-primary/10 to-transparent flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-primary-foreground shadow-lg shadow-primary/20">
              <Bot size={22} />
            </div>
            <div>
              <h3 className="font-bold text-sm">Expert Machine Guide</h3>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] uppercase font-black tracking-widest text-muted-foreground">Context Aware AI</span>
              </div>
            </div>
          </div>
          <button onClick={() => setIsOpen(false)} className="text-muted-foreground hover:text-foreground">
            <Minimize2 size={18} />
          </button>
        </div>

        {/* Message List */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth"
        >
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`flex gap-3 max-w-[85%] ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                <div className={`shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
                  msg.role === "assistant" ? "bg-muted text-muted-foreground" : "bg-primary text-primary-foreground"
                }`}>
                  {msg.role === "assistant" ? <Bot size={16} /> : <User size={16} />}
                </div>
                <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
                  msg.role === "assistant" 
                  ? "bg-muted/30 border border-border" 
                  : "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                }`}>
                  {msg.content}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
               <div className="flex gap-3 max-w-[85%]">
                <div className="shrink-0 w-8 h-8 rounded-lg bg-muted text-muted-foreground flex items-center justify-center">
                  <Bot size={16} />
                </div>
                <div className="p-4 rounded-2xl bg-muted/30 border border-border flex items-center gap-3">
                  <Loader2 size={16} className="animate-spin" />
                  <span className="text-xs text-muted-foreground italic">Analyzing machine state...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-6 border-t border-border bg-muted/10">
          <div className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask about the machine status..."
              className="w-full bg-background border border-border rounded-2xl py-3 pl-4 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="absolute right-2 top-2 p-1.5 rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:scale-105 active:scale-95 transition-all disabled:opacity-50"
            >
              <Send size={18} />
            </button>
          </div>
          <div className="mt-4 flex items-center gap-2 justify-center">
             <Sparkles size={12} className="text-primary" />
             <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Powered by Gemini 1.5 Flash</p>
          </div>
        </div>
      </div>
    </>
  );
}
