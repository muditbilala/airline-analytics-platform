import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { TrendData } from "../../api/analytics";
import ChartWrapper from "./ChartWrapper";

interface Props {
  data: TrendData[] | null;
  loading: boolean;
}

const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export default function MonthlyTrendChart({ data, loading }: Props) {
  const formatted = (data ?? []).map((d) => ({
    ...d,
    label: `${MONTH_NAMES[d.month - 1]} ${d.year}`,
  }));

  return (
    <ChartWrapper title="Monthly Delay Trends" loading={loading}>
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={formatted} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(204,214,246,0.06)" />
          <XAxis
            dataKey="label"
            tick={{ fill: "#8892b0", fontSize: 10 }}
            axisLine={{ stroke: "rgba(204,214,246,0.1)" }}
            interval="preserveStartEnd"
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis
            yAxisId="left"
            tick={{ fill: "#8892b0", fontSize: 12 }}
            axisLine={{ stroke: "rgba(204,214,246,0.1)" }}
            tickFormatter={(v: number) => `${v}%`}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fill: "#8892b0", fontSize: 12 }}
            axisLine={{ stroke: "rgba(204,214,246,0.1)" }}
            tickFormatter={(v: number) => `${v}m`}
          />
          <Tooltip
            contentStyle={{
              background: "rgba(17,34,64,0.95)",
              border: "1px solid rgba(204,214,246,0.15)",
              borderRadius: 8,
              color: "#ccd6f6",
            }}
          />
          <Legend wrapperStyle={{ color: "#8892b0", fontSize: 12 }} />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="delay_rate"
            stroke="#e85d3a"
            strokeWidth={2}
            dot={false}
            name="Delay Rate %"
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="avg_delay"
            stroke="#64ffda"
            strokeWidth={2}
            dot={false}
            name="Avg Delay (min)"
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
}
