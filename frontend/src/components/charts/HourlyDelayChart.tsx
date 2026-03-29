import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { HourlyDelay } from "../../api/analytics";
import ChartWrapper from "./ChartWrapper";

interface Props {
  data: HourlyDelay[] | null;
  loading: boolean;
}

export default function HourlyDelayChart({ data, loading }: Props) {
  return (
    <ChartWrapper title="Delay Rate by Hour of Day" loading={loading}>
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={data ?? []} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(204,214,246,0.06)" />
          <XAxis
            dataKey="hour"
            tick={{ fill: "#8892b0", fontSize: 12 }}
            tickFormatter={(h: number) => `${h}:00`}
            axisLine={{ stroke: "rgba(204,214,246,0.1)" }}
          />
          <YAxis
            tick={{ fill: "#8892b0", fontSize: 12 }}
            tickFormatter={(v: number) => `${v}%`}
            axisLine={{ stroke: "rgba(204,214,246,0.1)" }}
          />
          <Tooltip
            contentStyle={{
              background: "rgba(17,34,64,0.95)",
              border: "1px solid rgba(204,214,246,0.15)",
              borderRadius: 8,
              color: "#ccd6f6",
            }}
            formatter={(value: number) => [`${value.toFixed(1)}%`, "Delay Rate"]}
            labelFormatter={(label: number) => `${label}:00`}
          />
          <Bar
            dataKey="delay_rate"
            fill="#e85d3a"
            radius={[4, 4, 0, 0]}
            maxBarSize={30}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
}
