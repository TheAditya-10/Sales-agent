"use client";

import { FormEvent, useMemo, useRef, useState } from "react";
import { Bot, ChevronDown, Send, Sparkles, X } from "lucide-react";
import { API_URL } from "@/lib/api";
import { SalesStoryCard } from "@/components/SalesStoryCard";

type Answer = { doubt: string; answer: string };
type Message =
  | { role: "assistant"; kind: "text"; text: string }
  | { role: "assistant"; kind: "answers"; answers: Answer[] }
  | { role: "assistant"; kind: "handoff"; text: string }
  | { role: "user"; kind: "text"; text: string };

const STATUS_LABELS: Record<string, string> = {
  classifying_intent: "Reading buyer intent...",
  searching_web: "Searching live car sources...",
  comparing_specs: "Comparing specs and pricing...",
  synthesizing: "Writing the sales story...",
};

function conversationId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `demo-${Date.now()}`;
}

export function ChatWidget({ carContext }: { carContext: string }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("");
  const [handoffOpen, setHandoffOpen] = useState(false);
  const [leadName, setLeadName] = useState("");
  const [leadPhone, setLeadPhone] = useState("");
  const [leadSaved, setLeadSaved] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      kind: "text",
      text: "Hello! I'm your AutoElite concierge. How can I help you today with the XUV700?",
    },
  ]);
  const idRef = useRef(conversationId());
  const latestDoubts = useMemo(() => {
    return messages
      .filter((message): message is Extract<Message, { kind: "answers" }> => message.kind === "answers")
      .flatMap((message) => message.answers.map((answer) => answer.doubt))
      .slice(-3)
      .join("; ");
  }, [messages]);

  async function submitMessage(text: string) {
    const message = text.trim();
    if (!message || isStreaming) return;
    setInput("");
    setLeadSaved(false);
    setMessages((current) => [...current, { role: "user", kind: "text", text: message }]);
    setStatus("classifying_intent");
    setIsStreaming(true);

    try {
      const response = await fetch(`${API_URL}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          car_context: carContext,
          conversation_id: idRef.current,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error("Chat stream failed");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const rawEvent of events) {
          const parsed = parseSse(rawEvent);
          if (!parsed) continue;
          if (parsed.event === "status") {
            setStatus(parsed.data.status || "");
          }
          if (parsed.event === "request_handoff") {
            setHandoffOpen(true);
            setStatus("");
            setMessages((current) => [
              ...current,
              { role: "assistant", kind: "handoff", text: parsed.data.message },
            ]);
          }
          if (parsed.event === "final") {
            setStatus("");
            setMessages((current) => [
              ...current,
              { role: "assistant", kind: "answers", answers: parsed.data.answers || [] },
            ]);
          }
        }
      }
    } catch {
      setStatus("");
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          kind: "text",
          text: "I couldn't reach the assistant service right now. Please check that the backend is running.",
        },
      ]);
    } finally {
      setIsStreaming(false);
    }
  }

  async function saveLead(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const doubtsSummary = latestDoubts || "Requested consultant handoff from XUV700 catalog chat.";
    const response = await fetch(`${API_URL}/api/leads`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: leadName,
        phone: leadPhone,
        car_context: carContext,
        doubts_summary: doubtsSummary,
      }),
    });
    if (response.ok) {
      setLeadSaved(true);
      setHandoffOpen(false);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          kind: "text",
          text: "Done. Your lead is in the consultant panel and a dealership advisor can follow up.",
        },
      ]);
      setLeadName("");
      setLeadPhone("");
    }
  }

  return (
    <div className="fixed bottom-6 right-5 z-50 flex flex-col items-end md:bottom-8 md:right-8">
      {open ? (
        <div className="mb-4 flex h-[640px] w-[calc(100vw-40px)] max-w-[400px] flex-col overflow-hidden rounded-lg border border-outline-variant bg-white shadow-2xl">
          <div className="flex items-center justify-between bg-primary-container p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-white">
                <Sparkles size={16} />
              </div>
              <div>
                <div className="text-sm font-semibold text-white">AutoElite Assistant</div>
                <div className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-tertiary-fixed" />
                  <span className="text-[10px] font-medium text-on-primary-container">Active now</span>
                </div>
              </div>
            </div>
            <button
              aria-label="Close chat"
              className="text-on-primary-container transition hover:text-white"
              onClick={() => setOpen(false)}
            >
              <X size={20} />
            </button>
          </div>

          <div className="chat-scroll flex-1 space-y-4 overflow-y-auto bg-surface-container-lowest p-4">
            <div className="flex">
              <span className="rounded-full bg-secondary-container px-3 py-1 text-[11px] font-medium text-on-secondary-container">
                Chatting about: Mahindra XUV700
              </span>
            </div>
            {messages.map((message, index) => (
              <ChatMessage key={`${message.role}-${index}`} message={message} />
            ))}

            {status ? (
              <div className="rounded-lg border border-outline-variant bg-white p-3 shadow-sm">
                <div className="h-1 overflow-hidden rounded bg-surface-container">
                  <div className="shimmer h-full w-full" />
                </div>
                <p className="mt-2 text-[11px] font-medium text-secondary">
                  {STATUS_LABELS[status] || status}
                </p>
              </div>
            ) : null}

            {handoffOpen ? (
              <form
                onSubmit={saveLead}
                className="rounded-lg border border-outline-variant bg-white p-4 shadow-sm"
              >
                <p className="font-mono text-[10px] uppercase text-secondary">Confirm callback</p>
                <div className="mt-3 space-y-2">
                  <input
                    required
                    value={leadName}
                    onChange={(event) => setLeadName(event.target.value)}
                    className="w-full rounded-lg border border-outline-variant bg-surface-container-low px-3 py-2 text-sm outline-none focus:border-primary"
                    placeholder="Name"
                  />
                  <input
                    required
                    value={leadPhone}
                    onChange={(event) => setLeadPhone(event.target.value)}
                    className="w-full rounded-lg border border-outline-variant bg-surface-container-low px-3 py-2 text-sm outline-none focus:border-primary"
                    placeholder="Phone"
                  />
                </div>
                <button className="mt-3 w-full rounded-lg bg-primary px-4 py-2 text-sm font-medium text-on-primary">
                  Send to consultant
                </button>
              </form>
            ) : null}

            {leadSaved ? (
              <div className="rounded-lg bg-tertiary-fixed px-3 py-2 text-sm text-primary">
                Lead captured for consultant follow-up.
              </div>
            ) : null}

            <div className="flex flex-wrap gap-2 pt-2">
              {["Compare vs Creta", "ADAS Specs", "On-road price"].map((chip) => (
                <button
                  key={chip}
                  onClick={() => submitMessage(chip)}
                  className="rounded-full border border-outline-variant px-3 py-1.5 text-sm text-secondary transition hover:border-primary-container hover:bg-primary-container hover:text-white"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={(event) => { event.preventDefault(); submitMessage(input); }} className="border-t border-outline-variant bg-white p-4">
            <div className="flex items-center gap-2 rounded-lg bg-surface-container px-4 py-2">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                className="w-full border-none bg-transparent text-sm text-on-surface outline-none"
                placeholder="Ask anything..."
              />
              <button aria-label="Send message" className="text-primary" disabled={isStreaming}>
                <Send size={18} />
              </button>
            </div>
          </form>
        </div>
      ) : null}

      <button aria-label="Toggle chat" className="group relative" onClick={() => setOpen((value) => !value)}>
        <div className="pulse-ring absolute inset-0 rounded-full bg-primary" />
        <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-primary text-white shadow-2xl transition-transform group-hover:scale-110">
          {open ? <ChevronDown size={32} /> : <Bot size={32} />}
        </div>
      </button>
    </div>
  );
}

function ChatMessage({ message }: { message: Message }) {
  if (message.kind === "answers") {
    return (
      <div className="space-y-3">
        {message.answers.map((answer) => (
          <SalesStoryCard key={answer.doubt} card={answer} />
        ))}
      </div>
    );
  }

  if (message.kind === "handoff") {
    return (
      <div className="max-w-[88%] rounded-br-lg rounded-tl-lg rounded-tr-lg bg-surface-container p-3 text-sm leading-6 text-on-surface">
        {message.text}
      </div>
    );
  }

  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-lg p-3 text-sm leading-6 ${
          isUser
            ? "rounded-br-none bg-primary text-white"
            : "rounded-bl-none bg-surface-container text-on-surface"
        }`}
      >
        {message.text}
      </div>
    </div>
  );
}

function parseSse(raw: string): { event: string; data: any } | null {
  const event = raw.match(/^event: (.+)$/m)?.[1];
  const data = raw.match(/^data: (.+)$/m)?.[1];
  if (!event || !data) return null;
  try {
    return { event, data: JSON.parse(data) };
  } catch {
    return null;
  }
}
