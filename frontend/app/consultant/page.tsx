"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Filter, Phone, Search } from "lucide-react";
import { API_URL, CallCreateResponse, Lead } from "@/lib/api";
import { TopNav } from "@/components/TopNav";

const seedLeads: Lead[] = [
  {
    id: -1,
    name: "Aryan Sharma",
    phone: "+91 98765 43210",
    car_context: "Mahindra XUV700",
    doubts_summary: "Comparison with Safari/Creta",
    status: "NEW",
    created_at: new Date(Date.now() - 120000).toISOString(),
  },
  {
    id: -2,
    name: "Priya Varma",
    phone: "+91 87654 32109",
    car_context: "Mahindra XUV700",
    doubts_summary: "ADAS Level 2 safety features",
    status: "NEW",
    created_at: new Date(Date.now() - 900000).toISOString(),
  },
  {
    id: -3,
    name: "Rahul Nair",
    phone: "+91 76543 21098",
    car_context: "Mahindra XUV700",
    doubts_summary: "Financing options",
    status: "CALLED",
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
];

export default function ConsultantPage() {
  const [leads, setLeads] = useState<Lead[]>(seedLeads);
  const [query, setQuery] = useState("");
  const [calledIds, setCalledIds] = useState<Set<number>>(new Set([-3]));
  const [startingLeadId, setStartingLeadId] = useState<number | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const response = await fetch(`${API_URL}/api/leads`, { cache: "no-store" });
        if (!response.ok) return;
        const data = (await response.json()) as Lead[];
        if (active && data.length > 0) {
          setLeads([...data, ...seedLeads]);
        }
      } catch {
        // The static seed rows keep the dashboard useful if the backend is not running.
      }
    }

    load();
    const id = window.setInterval(load, 5000);
    return () => {
      active = false;
      window.clearInterval(id);
    };
  }, []);

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return leads;
    return leads.filter((lead) =>
      `${lead.name} ${lead.phone} ${lead.doubts_summary} ${lead.car_context}`.toLowerCase().includes(term),
    );
  }, [leads, query]);

  const newCount = filtered.filter((lead) => !calledIds.has(lead.id) && lead.status !== "CALLED").length;

  async function startCall(lead: Lead) {
    setStartingLeadId(lead.id);
    try {
      const response = await fetch(`${API_URL}/api/calls`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lead_id: lead.id }),
      });
      if (!response.ok) {
        throw new Error("Could not start call");
      }
      const call = (await response.json()) as CallCreateResponse;
      const customerUrl = buildCustomerUrl(call);
      const consultantUrl = `/call/consultant/${call.room_name}?customerUrl=${encodeURIComponent(customerUrl)}`;
      window.sessionStorage.setItem(`autoelite:${call.room_name}:consultant_token`, call.consultant_token);
      window.sessionStorage.setItem(`autoelite:${call.room_name}:livekit_url`, call.livekit_url);
      window.location.href = consultantUrl;
    } finally {
      setStartingLeadId(null);
    }
  }

  return (
    <main className="min-h-screen bg-background text-on-background">
      <TopNav panel />
      <div className="mx-auto w-full max-w-container-max px-margin-mobile py-stack-lg md:px-margin-desktop">
        <section className="mb-stack-lg flex flex-col justify-between gap-gutter md:flex-row md:items-end">
          <div>
            <h1 className="text-3xl font-semibold text-primary">Active Inquiries</h1>
            <p className="mt-1 text-secondary">Manage high-intent leads and schedule vehicle consultations.</p>
          </div>
          <div className="flex flex-col gap-stack-md sm:flex-row">
            <div className="flex items-center gap-2 rounded-DEFAULT border border-outline-variant bg-surface-container px-stack-md py-stack-sm">
              <Search size={18} className="text-secondary" />
              <input
                className="w-full border-none bg-transparent text-sm outline-none sm:w-48"
                placeholder="Search leads..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </div>
            <button className="flex items-center justify-center gap-2 rounded-DEFAULT border border-outline-variant bg-surface px-stack-md py-stack-sm text-sm font-medium text-on-surface transition hover:bg-surface-container-high">
              <Filter size={18} />
              Filter
            </button>
          </div>
        </section>

        <section className="mb-section-gap grid grid-cols-1 gap-gutter md:grid-cols-4">
          <Stat label="New Leads" value={String(newCount).padStart(2, "0")} />
          <Stat label="Called Today" value={String(calledIds.size + 27)} />
          <Stat label="Conv. Rate" value="18.4%" tone="success" />
          <Stat label="Pending Followups" value="04" tone="error" />
        </section>

        <section className="mb-section-gap overflow-hidden rounded-DEFAULT border border-outline-variant bg-white shadow-fintech">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1040px] border-collapse text-left">
              <thead className="border-b border-outline-variant bg-surface-container-low">
                <tr>
                  {["Name", "Contact", "Model", "Doubt Summary", "Timestamp", "Status", "Actions"].map((header) => (
                    <th key={header} className="px-stack-lg py-stack-md font-mono text-xs uppercase text-on-surface-variant">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant">
                {filtered.map((lead) => {
                  const called = calledIds.has(lead.id) || lead.status === "CALLED";
                  return (
                    <tr key={lead.id} className={`transition hover:bg-white ${called ? "opacity-60" : ""}`}>
                      <td className="px-stack-lg py-stack-lg">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary-container text-sm font-bold text-primary">
                            {initials(lead.name)}
                          </div>
                          <span className="text-sm font-semibold text-primary">{lead.name}</span>
                        </div>
                      </td>
                      <td className="px-stack-lg py-stack-lg font-mono text-xs text-secondary">{lead.phone}</td>
                      <td className="px-stack-lg py-stack-lg">
                        <span className="rounded-full border border-outline-variant bg-surface-variant px-3 py-1 font-mono text-[10px] uppercase text-on-surface-variant">
                          XUV700
                        </span>
                      </td>
                      <td className="max-w-xs truncate px-stack-lg py-stack-lg text-sm text-on-secondary-container">
                        &quot;{lead.doubts_summary}&quot;
                      </td>
                      <td className="px-stack-lg py-stack-lg text-sm text-secondary">{relativeTime(lead.created_at)}</td>
                      <td className="px-stack-lg py-stack-lg text-center">
                        <span
                          className={`rounded-full px-3 py-1 font-mono text-[10px] uppercase text-on-primary ${
                            called ? "bg-on-tertiary-container" : "bg-primary"
                          }`}
                        >
                          {called ? "Called" : "New"}
                        </span>
                      </td>
                      <td className="px-stack-lg py-stack-lg text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            disabled={startingLeadId === lead.id}
                            onClick={() => startCall(lead)}
                            className="inline-flex items-center justify-center gap-2 rounded-DEFAULT bg-primary px-4 py-2 text-sm font-medium text-on-primary transition active:scale-95 disabled:opacity-60 fintech-shadow-hover"
                          >
                            <Phone size={16} />
                            {startingLeadId === lead.id ? "Starting..." : "Start Call"}
                          </button>
                          <button
                            disabled={called}
                            onClick={() => setCalledIds((current) => new Set(current).add(lead.id))}
                            className={
                              called
                                ? "rounded-DEFAULT border border-outline-variant px-4 py-2 text-sm font-medium text-secondary"
                                : "rounded-DEFAULT border border-outline-variant bg-white px-4 py-2 text-sm font-medium text-on-surface transition hover:bg-surface-container"
                            }
                          >
                            {called ? "Call Logged" : "Mark Called"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between border-t border-outline-variant bg-surface-container-lowest px-stack-lg py-stack-md">
            <span className="text-sm text-secondary">Showing {filtered.length} of {leads.length} leads</span>
            <div className="flex items-center gap-2">
              <button className="flex h-8 w-8 items-center justify-center rounded-full border border-outline-variant text-secondary opacity-30">
                <ChevronLeft size={18} />
              </button>
              <button className="flex h-8 w-8 items-center justify-center rounded-full border border-outline-variant text-secondary transition hover:bg-surface-container">
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-gutter md:grid-cols-2">
          <div className="rounded-DEFAULT border border-outline-variant bg-white p-stack-lg shadow-fintech">
            <h3 className="mb-stack-md text-xl font-semibold text-primary">Lead Intent Analysis</h3>
            <IntentBar label="Feature Comparison" value={64} />
            <IntentBar label="Financing Queries" value={28} />
            <IntentBar label="Safety Features" value={12} />
          </div>
          <div className="flex flex-col justify-between rounded-DEFAULT border border-primary-container bg-primary-container p-stack-lg text-on-primary-container shadow-fintech">
            <div>
              <h3 className="mb-2 text-xl font-semibold text-on-primary">Automated Follow-ups</h3>
              <p className="leading-7 text-on-primary-container">
                System-level AI is currently handling 4 cold leads to re-engage interest.
              </p>
            </div>
            <div className="mt-stack-lg flex items-center justify-between">
              <div className="flex -space-x-3">
                {["bg-surface-container-high", "bg-surface-variant", "bg-outline-variant"].map((className) => (
                  <div key={className} className={`h-10 w-10 rounded-full border-2 border-primary-container ${className}`} />
                ))}
                <div className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-primary-container bg-primary text-[10px] text-on-primary">
                  +4
                </div>
              </div>
              <button className="border-b border-on-primary text-sm font-medium text-on-primary">
                View Automation Log
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function buildCustomerUrl(call: CallCreateResponse) {
  const origin = window.location.origin;
  const params = new URLSearchParams({
    token: call.customer_token,
    livekitUrl: call.livekit_url,
  });
  return `${origin}/call/customer/${call.room_name}?${params.toString()}`;
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: "success" | "error" }) {
  return (
    <div className="rounded-DEFAULT border border-outline-variant bg-white p-stack-lg shadow-fintech">
      <p className="mb-2 font-mono text-xs uppercase text-on-secondary-container">{label}</p>
      <p className={`text-3xl font-semibold ${tone === "success" ? "text-on-tertiary-container" : tone === "error" ? "text-error" : "text-primary"}`}>
        {value}
      </p>
    </div>
  );
}

function IntentBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="mb-4 space-y-1">
      <div className="flex justify-between text-sm font-medium">
        <span>{label}</span>
        <span className="font-bold text-primary">{value}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-container-high">
        <div className="h-full rounded-full bg-primary" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function relativeTime(value: string) {
  const ms = Date.now() - new Date(value).getTime();
  const minutes = Math.max(1, Math.round(ms / 60000));
  if (minutes < 60) return `${minutes}m ago`;
  return `${Math.round(minutes / 60)}h ago`;
}
