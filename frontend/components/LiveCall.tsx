"use client";

import { useCallback, useMemo, useState } from "react";
import {
  ControlBar,
  LiveKitRoom,
  ParticipantTile,
  RoomAudioRenderer,
  useDataChannel,
  useTracks,
} from "@livekit/components-react";
import { Copy, PhoneOff } from "lucide-react";
import { Track } from "livekit-client";
import { SalesStoryCard, SalesStoryCardData } from "@/components/SalesStoryCard";

const INSIGHT_TOPIC = "autoelite.insight";

type LiveCallProps = {
  role: "consultant" | "customer";
  roomId: string;
  token: string | null;
  livekitUrl: string | null;
  customerUrl?: string | null;
};

export function LiveCall({ role, roomId, token, livekitUrl, customerUrl }: LiveCallProps) {
  const [connected, setConnected] = useState(true);

  if (!token || !livekitUrl) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-margin-mobile text-on-background">
        <div className="max-w-md rounded-DEFAULT border border-outline-variant bg-white p-stack-lg shadow-fintech">
          <p className="font-mono text-xs uppercase text-secondary">Missing call credentials</p>
          <p className="mt-2 text-sm leading-6 text-on-surface-variant">
            Start this room from the consultant panel so the browser has a LiveKit token.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background text-on-background">
      <LiveKitRoom
        token={token}
        serverUrl={livekitUrl}
        connect={connected}
        audio
        video
        onDisconnected={() => setConnected(false)}
        className="min-h-screen"
      >
        <RoomAudioRenderer />
        {role === "consultant" ? (
          <ConsultantCall roomId={roomId} customerUrl={customerUrl} onLeave={() => setConnected(false)} />
        ) : (
          <CustomerCall roomId={roomId} onLeave={() => setConnected(false)} />
        )}
      </LiveKitRoom>
    </main>
  );
}

function ConsultantCall({
  roomId,
  customerUrl,
  onLeave,
}: {
  roomId: string;
  customerUrl?: string | null;
  onLeave: () => void;
}) {
  const [insights, setInsights] = useState<SalesStoryCardData[]>([]);

  const onMessage = useCallback((message: { payload: Uint8Array }) => {
    try {
      const raw = new TextDecoder().decode(message.payload);
      const parsed = JSON.parse(raw) as SalesStoryCardData & { type?: string };
      if (parsed.type !== "sales_story" || !parsed.doubt || !parsed.answer) return;
      setInsights((current) => [parsed, ...current].slice(0, 12));
    } catch {
      // Ignore malformed demo data channel packets.
    }
  }, []);

  useDataChannel(INSIGHT_TOPIC, onMessage);

  return (
    <div className="mx-auto grid min-h-screen w-full max-w-container-max gap-gutter px-margin-mobile py-stack-lg md:grid-cols-[minmax(0,1fr)_420px] md:px-margin-desktop">
      <section className="flex min-h-[560px] flex-col overflow-hidden rounded-DEFAULT border border-outline-variant bg-white shadow-fintech">
        <div className="border-b border-outline-variant bg-surface-container-low px-stack-lg py-stack-md">
          <p className="font-mono text-xs uppercase text-on-secondary-container">Browser call</p>
          <h1 className="mt-1 text-2xl font-semibold text-primary">Live XUV700 Consultation</h1>
          {customerUrl ? <CopyableCustomerLink value={customerUrl} /> : null}
        </div>
        <CallStage preferredIdentity="customer" emptyText="Waiting for the customer to join" />
        <div className="border-t border-outline-variant bg-surface-container-lowest p-stack-md">
          <ControlBar controls={{ chat: false, screenShare: false }} />
        </div>
      </section>

      <aside className="flex min-h-[560px] flex-col rounded-DEFAULT border border-outline-variant bg-surface-container-lowest shadow-fintech">
        <div className="border-b border-outline-variant bg-white px-stack-lg py-stack-md">
          <p className="font-mono text-xs uppercase text-on-secondary-container">Room {roomId}</p>
          <h2 className="mt-1 text-2xl font-semibold text-primary">Surfaced Insights</h2>
        </div>
        <div className="chat-scroll flex-1 space-y-3 overflow-y-auto p-stack-md">
          {insights.length > 0 ? (
            insights.map((card, index) => (
              <SalesStoryCard key={`${card.category || card.doubt}-${card.timestamp || index}`} card={card} />
            ))
          ) : (
            <div className="rounded-lg border border-outline-variant bg-white p-4 text-sm leading-6 text-on-surface-variant shadow-sm">
              Customer objections detected during the call will appear here.
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}

function CustomerCall({ onLeave }: { roomId: string; onLeave: () => void }) {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-margin-mobile py-stack-lg md:px-margin-desktop">
      <header className="mb-stack-md">
        <p className="font-mono text-xs uppercase text-on-secondary-container">Connecting you with a consultant</p>
        <h1 className="mt-1 text-2xl font-semibold text-primary">Live XUV700 Consultation</h1>
      </header>
      <section className="flex min-h-[560px] flex-1 flex-col overflow-hidden rounded-DEFAULT border border-outline-variant bg-white shadow-fintech">
        <CallStage preferredIdentity="consultant" emptyText="Waiting for the consultant to join" />
        <div className="border-t border-outline-variant bg-surface-container-lowest p-stack-md">
          <ControlBar controls={{ chat: false, screenShare: false }} />
          <button
            onClick={onLeave}
            className="mt-3 inline-flex items-center gap-2 rounded-DEFAULT border border-outline-variant px-4 py-2 text-sm font-medium text-secondary transition hover:bg-surface-container"
          >
            <PhoneOff size={16} />
            Leave
          </button>
        </div>
      </section>
    </div>
  );
}

function CallStage({ preferredIdentity, emptyText }: { preferredIdentity: string; emptyText: string }) {
  const tracks = useTracks([{ source: Track.Source.Camera, withPlaceholder: true }], {
    onlySubscribed: false,
  });
  const selectedTrack = useMemo(() => {
    return (
      tracks.find((trackRef) => trackRef.participant.identity === preferredIdentity) ||
      tracks.find((trackRef) => !trackRef.participant.isLocal) ||
      tracks[0]
    );
  }, [preferredIdentity, tracks]);

  return (
    <div className="flex flex-1 items-center justify-center bg-primary-container p-stack-md">
      {selectedTrack ? (
        <ParticipantTile
          trackRef={selectedTrack}
          className="h-full min-h-[420px] w-full overflow-hidden rounded-DEFAULT border border-outline-variant bg-primary text-on-primary"
        />
      ) : (
        <div className="rounded-lg border border-outline-variant bg-white p-4 text-sm text-on-surface-variant">
          {emptyText}
        </div>
      )}
    </div>
  );
}

function CopyableCustomerLink({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <div className="mt-3 flex flex-col gap-2 rounded-lg border border-outline-variant bg-white p-3 sm:flex-row sm:items-center">
      <input
        readOnly
        value={value}
        className="min-w-0 flex-1 bg-transparent font-mono text-[11px] text-on-surface-variant outline-none"
      />
      <button
        onClick={copy}
        className="inline-flex items-center justify-center gap-2 rounded-DEFAULT bg-primary px-3 py-2 text-xs font-medium text-on-primary transition active:scale-95"
      >
        <Copy size={14} />
        {copied ? "Copied" : "Copy"}
      </button>
    </div>
  );
}
