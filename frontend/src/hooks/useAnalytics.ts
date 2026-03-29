/**
 * React hooks for fetching analytics data from the backend API.
 */

import { useState, useEffect } from "react";
import {
  fetchOverview,
  fetchHourlyDelays,
  fetchCarrierPerformance,
  fetchDelayCauses,
  fetchMonthlyTrends,
  fetchHeatmap,
} from "../api/analytics";
import type {
  KPIOverview,
  HourlyDelay,
  CarrierDelay,
  DelayCause,
  TrendData,
  HeatmapCell,
} from "../api/analytics";

// ---------------------------------------------------------------------------
// Full analytics hook (used by Insights page)
// ---------------------------------------------------------------------------

interface AnalyticsState {
  overview: KPIOverview | null;
  hourly: HourlyDelay[] | null;
  carriers: CarrierDelay[] | null;
  causes: DelayCause[] | null;
  trends: TrendData[] | null;
  heatmap: HeatmapCell[] | null;
  loading: boolean;
  error: string | null;
}

export function useAnalytics(): AnalyticsState {
  const [state, setState] = useState<AnalyticsState>({
    overview: null,
    hourly: null,
    carriers: null,
    causes: null,
    trends: null,
    heatmap: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [overview, hourly, carriers, causes, trends, heatmap] =
          await Promise.all([
            fetchOverview(),
            fetchHourlyDelays(),
            fetchCarrierPerformance(),
            fetchDelayCauses(),
            fetchMonthlyTrends(),
            fetchHeatmap(),
          ]);

        if (!cancelled) {
          setState({
            overview,
            hourly,
            carriers,
            causes,
            trends,
            heatmap,
            loading: false,
            error: null,
          });
        }
      } catch (err) {
        if (!cancelled) {
          setState((prev) => ({
            ...prev,
            loading: false,
            error:
              err instanceof Error
                ? err.message
                : "Failed to load analytics data. Make sure the backend is running on port 8000.",
          }));
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

// ---------------------------------------------------------------------------
// Dashboard hook (subset of data used by Dashboard page)
// ---------------------------------------------------------------------------

interface DashboardState {
  hourly: HourlyDelay[] | null;
  carriers: CarrierDelay[] | null;
  causes: DelayCause[] | null;
  trends: TrendData[] | null;
  loading: boolean;
  error: string | null;
}

export function useDashboardData(): DashboardState {
  const [state, setState] = useState<DashboardState>({
    hourly: null,
    carriers: null,
    causes: null,
    trends: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [hourly, carriers, causes, trends] = await Promise.all([
          fetchHourlyDelays(),
          fetchCarrierPerformance(),
          fetchDelayCauses(),
          fetchMonthlyTrends(),
        ]);

        if (!cancelled) {
          setState({ hourly, carriers, causes, trends, loading: false, error: null });
        }
      } catch (err) {
        if (!cancelled) {
          setState((prev) => ({
            ...prev,
            loading: false,
            error:
              err instanceof Error
                ? err.message
                : "Failed to load dashboard data. Make sure the backend is running.",
          }));
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
