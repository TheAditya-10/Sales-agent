import { Sparkles } from "lucide-react";

export type SalesStoryCardData = {
  doubt: string;
  answer: string;
  category?: string;
  timestamp?: string;
};

export function SalesStoryCard({ card }: { card: SalesStoryCardData }) {
  return (
    <div className="rounded-lg border border-outline-variant bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between gap-3">
        <span className="font-mono text-[10px] uppercase text-secondary">
          {card.category ? readableCategory(card.category) : "Sales story"}
        </span>
        <div className="flex items-center gap-2">
          {card.timestamp ? (
            <span className="font-mono text-[10px] uppercase text-on-secondary-container">
              {formatTime(card.timestamp)}
            </span>
          ) : null}
          <Sparkles size={14} className="text-primary" />
        </div>
      </div>
      <p className="mb-2 text-sm font-semibold text-primary">{card.doubt}</p>
      <p className="text-sm leading-6 text-on-surface-variant">{card.answer}</p>
    </div>
  );
}

function readableCategory(value: string) {
  return value.replace(/_/g, " ");
}

function formatTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
