/**
 * API client for the Flight Delay Analytics backend.
 *
 * All functions hit the FastAPI server and return typed data.
 * Base URL defaults to http://localhost:8000 but can be overridden
 * with the VITE_API_URL environment variable.
 */

const _raw = import.meta.env.VITE_API_URL;
const BASE: string =
  typeof _raw === "string" && _raw.trim().length > 0
    ? _raw.replace(/\/$/, "")   // strip any trailing slash
    : "http://localhost:8000";

// ---------------------------------------------------------------------------
// Shared types (mirror backend Pydantic schemas)
// ---------------------------------------------------------------------------

export interface KPIOverview {
  total_flights: number;
  on_time_pct: number;
  delay_pct: number;
  cancel_pct: number;
  avg_delay_min: number;
}

export interface HourlyDelay {
  hour: number;
  delay_rate: number;
  avg_delay: number;
  flight_count: number;
}

export interface CarrierDelay {
  carrier_code: string;
  carrier_name: string;
  total_flights: number;
  on_time_pct: number;
  avg_delay: number;
  rank: number;
}

export interface DelayCause {
  cause: string;
  total_minutes: number;
  percentage: number;
}

export interface TrendData {
  year: number;
  month: number;
  delay_rate: number;
  avg_delay: number;
  total_flights: number;
}

export interface HeatmapCell {
  hour: number;
  day_of_week: number;
  delay_rate: number;
  flight_count: number;
}

export interface ChatResponse {
  answer: string;
  data?: unknown;
  chart_type?: string;
}

// ---------------------------------------------------------------------------
// Wrapper around the standard API response envelope
// ---------------------------------------------------------------------------

interface APIEnvelope<T> {
  success: boolean;
  data: T;
  message: string;
  count: number | null;
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText}`);
  const json: APIEnvelope<T> = await res.json();
  if (!json.success) throw new Error(json.message || "API returned an error");
  return json.data;
}

// ---------------------------------------------------------------------------
// Analytics endpoints
// ---------------------------------------------------------------------------

export function fetchOverview(): Promise<KPIOverview> {
  return apiFetch<KPIOverview>("/api/v1/analytics/overview");
}

export function fetchHourlyDelays(): Promise<HourlyDelay[]> {
  return apiFetch<HourlyDelay[]>("/api/v1/analytics/delays/by-hour");
}

export function fetchCarrierPerformance(): Promise<CarrierDelay[]> {
  return apiFetch<CarrierDelay[]>("/api/v1/analytics/delays/by-carrier");
}

export function fetchDelayCauses(): Promise<DelayCause[]> {
  return apiFetch<DelayCause[]>("/api/v1/analytics/delays/causes");
}

export function fetchMonthlyTrends(): Promise<TrendData[]> {
  return apiFetch<TrendData[]>("/api/v1/analytics/delays/trends");
}

export function fetchHeatmap(): Promise<HeatmapCell[]> {
  return apiFetch<HeatmapCell[]>("/api/v1/analytics/delays/heatmap");
}

// ---------------------------------------------------------------------------
// Chatbot endpoints
// ---------------------------------------------------------------------------

export async function sendChatQuery(message: string): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/api/v1/chatbot/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error(`Chat error ${res.status}`);
  const json = await res.json();
  return json.data ?? json;
}

export async function fetchChatSuggestions(): Promise<string[]> {
  const res = await fetch(`${BASE}/api/v1/chatbot/suggestions`);
  if (!res.ok) throw new Error(`Suggestions error ${res.status}`);
  const json = await res.json();
  return json.data ?? json;
}
