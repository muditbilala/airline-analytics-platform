import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { CarrierDelay } from "../../api/analytics";
import ChartWrapper from "./ChartWrapper";

interface Props {
  data: CarrierDelay[] | null;
  loading: boolean;
}

export default function CarrierRankChart({ data, loading }: Props) {
  const sorted = data
    ? [...data].sort((a, b) => a.avg_delay - b.avg_delay).slice(0, 15)
    : [];

  return (
    <ChartWrapper title="Carrier Performance - Average Delay (min)" loading={loading}>
      <ResponsiveContainer width="100%" height={Math.max(350, sorted.length * 32)}>
        <BarChart
          data={sorted}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 10, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(204,214,246,0.06)" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fill: "#8892b0", fontSize: 12 }}
            axisLine={{ stroke: "rgba(204,214,246,0.1)" }}
            tickFormatter={(v: number) => `${v}m`}
          />
          <YAxis
            type="category"
            dataKey="carrier_name"
            tick={{ fill: "#ccd6f6", fontSize: 11 }}
            width={120}
            axisLine={{ stroke: "rgba(204,214,246,0.1)" }}
          />
          <Tooltip
            contentStyle={{
              background: "rgba(17,34,64,0.95)",
              border: "1px solid rgba(204,214,246,0.15)",
              borderRadius: 8,
              color: "#ccd6f6",
            }}
            formatter={(value: number) => [`${value.toFixed(1)} min`, "Avg Delay"]}
          />
          <Bar dataKey="avg_delay" fill="#64ffda" radius={[0, 4, 4, 0]} maxBarSize={24} />
        </BarChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
}
