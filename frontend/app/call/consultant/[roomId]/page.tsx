"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { LiveCall } from "@/components/LiveCall";

export default function ConsultantCallPage() {
  const params = useParams<{ roomId: string }>();
  const searchParams = useSearchParams();
  const roomId = params.roomId;
  const [token, setToken] = useState<string | null>(null);
  const [livekitUrl, setLivekitUrl] = useState<string | null>(null);

  useEffect(() => {
    setToken(window.sessionStorage.getItem(`autoelite:${roomId}:consultant_token`));
    setLivekitUrl(window.sessionStorage.getItem(`autoelite:${roomId}:livekit_url`));
  }, [roomId]);

  return (
    <LiveCall
      role="consultant"
      roomId={roomId}
      token={token}
      livekitUrl={livekitUrl}
      customerUrl={searchParams.get("customerUrl")}
    />
  );
}
