import apiClient from "./client";

export interface OverviewData {
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

export interface AirportDelay {
  airport_code: string;
  airport_name: string;
  total_flights: number;
  delay_rate: number;
  avg_delay: number;
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
  day_of_week: number;
  hour: number;
  delay_rate: number;
}

export interface ChatResponse {
  answer: string;
  data: unknown;
  chart_type: string;
}

export const fetchOverview = () =>
  apiClient.get<OverviewData>("/analytics/overview").then((r) => r.data);

export const fetchHourlyDelays = () =>
  apiClient.get<HourlyDelay[]>("/analytics/delays/by-hour").then((r) => r.data);

export const fetchCarrierDelays = () =>
  apiClient
    .get<CarrierDelay[]>("/analytics/delays/by-carrier")
    .then((r) => r.data);

export const fetchAirportDelays = () =>
  apiClient
    .get<AirportDelay[]>("/analytics/delays/by-airport")
    .then((r) => r.data);

export const fetchDelayCauses = () =>
  apiClient.get<DelayCause[]>("/analytics/delays/causes").then((r) => r.data);

export const fetchTrends = () =>
  apiClient.get<TrendData[]>("/analytics/delays/trends").then((r) => r.data);

export const fetchHeatmap = () =>
  apiClient.get<HeatmapCell[]>("/analytics/delays/heatmap").then((r) => r.data);

export const sendChatQuery = (message: string) =>
  apiClient
    .post<ChatResponse>("/chatbot/query", { message })
    .then((r) => r.data);

export const fetchChatSuggestions = () =>
  apiClient.get<string[]>("/chatbot/suggestions").then((r) => r.data);
