import { useEffect, useState } from "react";
import {
  fetchOverview,
  fetchHourlyDelays,
  fetchCarrierDelays,
  fetchDelayCauses,
  fetchTrends,
  fetchHeatmap,
  fetchAirportDelays,
} from "../api/analytics";
import type {
  OverviewData,
  HourlyDelay,
  CarrierDelay,
  DelayCause,
  TrendData,
  HeatmapCell,
  AirportDelay,
} from "../api/analytics";

interface AnalyticsState {
  overview: OverviewData | null;
  hourly: HourlyDelay[] | null;
  carriers: CarrierDelay[] | null;
  causes: DelayCause[] | null;
  trends: TrendData[] | null;
  heatmap: HeatmapCell[] | null;
  airports: AirportDelay[] | null;
  loading: boolean;
  error: string | null;
}

export function useAnalytics() {
  const [state, setState] = useState<AnalyticsState>({
    overview: null,
    hourly: null,
    carriers: null,
    causes: null,
    trends: null,
    heatmap: null,
    airports: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    setState((s) => ({ ...s, loading: true, error: null }));
    Promise.all([
      fetchOverview().catch(() => null),
      fetchHourlyDelays().catch(() => null),
      fetchCarrierDelays().catch(() => null),
      fetchDelayCauses().catch(() => null),
      fetchTrends().catch(() => null),
      fetchHeatmap().catch(() => null),
      fetchAirportDelays().catch(() => null),
    ])
      .then(([ov, hr, ca, cs, tr, hm, ap]) => {
        const allNull = !ov && !hr && !ca && !cs && !tr && !hm && !ap;
        setState({
          overview: ov,
          hourly: hr,
          carriers: ca,
          causes: cs,
          trends: tr,
          heatmap: hm,
          airports: ap,
          loading: false,
          error: allNull
            ? "Unable to load data. Please ensure the backend is running."
            : null,
        });
      })
      .catch(() => {
        setState((s) => ({
          ...s,
          loading: false,
          error: "Failed to fetch analytics data.",
        }));
      });
  }, []);

  return state;
}

export function useOverview() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverview()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading };
}

export function useDashboardData() {
  const [hourly, setHourly] = useState<HourlyDelay[] | null>(null);
  const [carriers, setCarriers] = useState<CarrierDelay[] | null>(null);
  const [causes, setCauses] = useState<DelayCause[] | null>(null);
  const [trends, setTrends] = useState<TrendData[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchHourlyDelays().catch(() => null),
      fetchCarrierDelays().catch(() => null),
      fetchDelayCauses().catch(() => null),
      fetchTrends().catch(() => null),
    ])
      .then(([h, c, cs, t]) => {
        setHourly(h);
        setCarriers(c);
        setCauses(cs);
        setTrends(t);
        if (!h && !c && !cs && !t) {
          setError("Unable to load dashboard data. Is the backend running?");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  return { hourly, carriers, causes, trends, loading, error };
}
