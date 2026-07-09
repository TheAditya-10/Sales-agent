"use client";

import { useParams, useSearchParams } from "next/navigation";
import { LiveCall } from "@/components/LiveCall";

export default function CustomerCallPage() {
  const params = useParams<{ roomId: string }>();
  const searchParams = useSearchParams();
  const roomId = params.roomId;
  const token = searchParams.get("token");
  const livekitUrl = searchParams.get("livekitUrl");

  return <LiveCall role="customer" roomId={roomId} token={token} livekitUrl={livekitUrl} />;
}
