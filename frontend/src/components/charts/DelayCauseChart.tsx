import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { DelayCause } from "../../api/analytics";
import ChartWrapper from "./ChartWrapper";

interface Props {
  data: DelayCause[] | null;
  loading: boolean;
}

const COLORS = ["#e85d3a", "#64ffda", "#ffd166", "#ff6b6b", "#8892b0", "#f07856", "#ccd6f6"];

export default function DelayCauseChart({ data, loading }: Props) {
  return (
    <ChartWrapper title="Delay Causes Breakdown" loading={loading}>
      <ResponsiveContainer width="100%" height={350}>
        <PieChart>
          <Pie
            data={data ?? []}
            dataKey="percentage"
            nameKey="cause"
            cx="50%"
            cy="50%"
            innerRadius={70}
            outerRadius={120}
            paddingAngle={3}
            strokeWidth={0}
          >
            {(data ?? []).map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "rgba(17,34,64,0.95)",
              border: "1px solid rgba(204,214,246,0.15)",
              borderRadius: 8,
              color: "#ccd6f6",
            }}
            formatter={(value: number) => [`${value.toFixed(1)}%`, "Share"]}
          />
          <Legend
            wrapperStyle={{ color: "#8892b0", fontSize: 12 }}
          />
        </PieChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
}
