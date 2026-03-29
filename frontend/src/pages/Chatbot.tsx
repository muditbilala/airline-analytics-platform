import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { sendChatQuery, fetchChatSuggestions } from "../api/analytics";
import type { ChatResponse } from "../api/analytics";
import ChatResponseChart from "../components/charts/ChatResponseChart";

interface Message {
  id: string;
  role: "user" | "bot";
  text: string;
  data?: unknown;
  chartType?: string;
}

export default function Chatbot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchChatSuggestions()
      .then(setSuggestions)
      .catch(() =>
        setSuggestions([
          "Which airline has the most delays?",
          "What is the busiest airport?",
          "What are the main causes of delays?",
          "Show delay trends over time",
          "What time of day has the most delays?",
        ])
      );
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const send = async (text: string) => {
    if (!text.trim() || sending) return;
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      text: text.trim(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const res: ChatResponse = await sendChatQuery(text.trim());
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "bot",
        text: res.answer,
        data: res.data,
        chartType: res.chart_type,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "bot",
          text: "Sorry, I encountered an error processing your request. Please make sure the backend is running.",
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="pt-20 pb-4 px-4 flex flex-col h-screen">
      <div className="max-w-4xl mx-auto w-full flex flex-col flex-1 min-h-0">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-4 shrink-0"
        >
          <h1 className="text-2xl sm:text-3xl font-bold text-text-bright mb-1">
            AI Chat Assistant
          </h1>
          <p className="text-text-secondary text-sm">
            Ask questions about flight delays, carriers, airports, and more
          </p>
        </motion.div>

        {/* Chat area */}
        <div className="glass-card flex-1 flex flex-col min-h-0 overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
            {messages.length === 0 && !sending && (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center mb-4">
                  <svg
                    className="w-8 h-8 text-accent"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
                    />
                  </svg>
                </div>
                <h3 className="text-text-bright font-semibold mb-2">
                  Start a Conversation
                </h3>
                <p className="text-text-secondary text-sm max-w-sm mb-6">
                  Ask anything about flight operations data. Try one of the
                  suggestions below.
                </p>

                {/* Suggestions */}
                <div className="flex flex-wrap justify-center gap-2 max-w-lg">
                  {suggestions.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="px-3 py-1.5 text-xs rounded-full bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20 transition-colors"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <AnimatePresence>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`flex ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[85%] sm:max-w-[75%] ${
                      msg.role === "user"
                        ? "bg-accent/20 border border-accent/20 rounded-2xl rounded-br-md"
                        : "bg-navy-lighter/50 border border-white/5 rounded-2xl rounded-bl-md"
                    } px-4 py-3`}
                  >
                    {msg.role === "bot" && (
                      <div className="flex items-center gap-2 mb-1.5">
                        <div className="w-5 h-5 rounded-full bg-blue/20 flex items-center justify-center">
                          <svg
                            className="w-3 h-3 text-blue-light"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth={2}
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"
                            />
                          </svg>
                        </div>
                        <span className="text-xs text-text-secondary font-medium">
                          FlightIQ
                        </span>
                      </div>
                    )}
                    <p className="text-sm text-text-primary whitespace-pre-wrap leading-relaxed">
                      {msg.text}
                    </p>
                    {msg.role === "bot" && msg.data && msg.chartType && (
                      <ChatResponseChart
                        chartType={msg.chartType}
                        data={msg.data}
                      />
                    )}
                    {msg.role === "bot" &&
                      msg.data &&
                      !msg.chartType &&
                      renderTable(msg.data)}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Typing indicator */}
            {sending && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="bg-navy-lighter/50 border border-white/5 rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-1.5">
                  <div className="typing-dot w-2 h-2 rounded-full bg-text-secondary" />
                  <div className="typing-dot w-2 h-2 rounded-full bg-text-secondary" />
                  <div className="typing-dot w-2 h-2 rounded-full bg-text-secondary" />
                </div>
              </motion.div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Suggestion chips when there are messages */}
          {messages.length > 0 && suggestions.length > 0 && (
            <div className="px-4 sm:px-6 pb-2 flex gap-2 overflow-x-auto shrink-0">
              {suggestions.slice(0, 4).map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  disabled={sending}
                  className="px-3 py-1 text-xs rounded-full bg-white/5 text-text-secondary border border-white/5 hover:bg-white/10 hover:text-text-primary transition-colors whitespace-nowrap shrink-0 disabled:opacity-50"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="p-3 sm:p-4 border-t border-white/5 shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                send(input);
              }}
              className="flex gap-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about flight delays..."
                disabled={sending}
                className="flex-1 bg-navy/50 border border-white/10 rounded-xl px-4 py-3 text-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20 transition-colors disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!input.trim() || sending}
                className="px-4 py-3 bg-accent hover:bg-accent-light disabled:bg-accent/30 disabled:cursor-not-allowed rounded-xl text-white transition-colors shrink-0"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
                  />
                </svg>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

function renderTable(data: unknown): React.ReactNode {
  if (!data || !Array.isArray(data) || data.length === 0) return null;
  const rows = data as Record<string, unknown>[];
  const keys = Object.keys(rows[0]);

  return (
    <div className="mt-3 overflow-x-auto rounded-lg border border-white/5">
      <table className="w-full text-xs text-text-secondary">
        <thead>
          <tr className="bg-navy/50">
            {keys.map((k) => (
              <th
                key={k}
                className="text-left px-3 py-2 border-b border-white/10 text-text-primary font-medium"
              >
                {k}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 20).map((row, i) => (
            <tr key={i} className="hover:bg-white/5 transition-colors">
              {keys.map((k) => (
                <td key={k} className="px-3 py-1.5 border-b border-white/5">
                  {typeof row[k] === "number"
                    ? (row[k] as number).toFixed(2)
                    : String(row[k])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
