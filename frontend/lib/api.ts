export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export type Lead = {
  id: number;
  name: string;
  phone: string;
  car_context: string;
  doubts_summary: string;
  status: string;
  created_at: string;
};
