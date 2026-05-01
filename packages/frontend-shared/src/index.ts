export type RiskLevel = "P0" | "P1" | "P2" | "P3" | "P4";

export interface DashboardMessage<T = Record<string, unknown>> {
  type: string;
  data: T;
  timestamp: string;
}

export interface HmiPrompt {
  prompt_id: string;
  event_id: string;
  elder_id: string;
  risk_level: RiskLevel;
  event_type: string;
  message: string;
  options: string[];
  timeout_sec: number;
  expires_at?: string;
}

declare global {
  interface ImportMeta {
    readonly env: Record<string, string | undefined>;
  }
}

export const API_BASE = import.meta.env.VITE_GUARDIAN_API_BASE ?? "http://localhost:8000";

export function wsUrl(): string {
  const url = new URL(API_BASE);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = "/ws/dashboard";
  return url.toString();
}
