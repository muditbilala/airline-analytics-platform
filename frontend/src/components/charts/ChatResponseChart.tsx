import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Props {
  chartType: string;
  data: unknown;
}

const COLORS = ["#e85d3a", "#64ffda", "#ffd166", "#ff6b6b", "#8892b0", "#f07856"];

export default function ChatResponseChart({ chartType, data }: Props) {
  if (!data || !Array.isArray(data) || data.length === 0) return null;

  const chartData = data as Record<string, unknown>[];
  const keys = Object.keys(chartData[0]).filter(
    (k) => typeof chartData[0][k] === "number"
  );
  const labelKey = Object.keys(chartData[0]).find(
    (k) => typeof chartData[0][k] === "string"
  ) ?? keys[0];

  const tooltipStyle = {
    background: "rgba(17,34,64,0.95)",
    border: "1px solid rgba(204,214,246,0.15)",
    borderRadius: 8,
    color: "#ccd6f6",
  };

  if (chartType === "bar") {
    return (
      <div className="mt-3 bg-navy/50 rounded-xl p-4">
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(204,214,246,0.06)" />
            <XAxis dataKey={labelKey} tick={{ fill: "#8892b0", fontSize: 11 }} />
            <YAxis tick={{ fill: "#8892b0", fontSize: 11 }} />
            <Tooltip contentStyle={tooltipStyle} />
            {keys.slice(0, 3).map((k, i) => (
              <Bar key={k} dataKey={k} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chartType === "line") {
    return (
      <div className="mt-3 bg-navy/50 rounded-xl p-4">
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(204,214,246,0.06)" />
            <XAxis dataKey={labelKey} tick={{ fill: "#8892b0", fontSize: 11 }} />
            <YAxis tick={{ fill: "#8892b0", fontSize: 11 }} />
            <Tooltip contentStyle={tooltipStyle} />
            {keys.slice(0, 3).map((k, i) => (
              <Line
                key={k}
                type="monotone"
                dataKey={k}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chartType === "pie") {
    const valueKey = keys[0];
    return (
      <div className="mt-3 bg-navy/50 rounded-xl p-4">
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={chartData}
              dataKey={valueKey}
              nameKey={labelKey}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={90}
              paddingAngle={3}
              strokeWidth={0}
            >
              {chartData.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // Fallback: render as table
  return (
    <div className="mt-3 overflow-x-auto">
      <table className="w-full text-xs text-text-secondary">
        <thead>
          <tr>
            {Object.keys(chartData[0]).map((k) => (
              <th key={k} className="text-left px-2 py-1 border-b border-white/10 text-text-primary">
                {k}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {chartData.slice(0, 20).map((row, i) => (
            <tr key={i}>
              {Object.values(row).map((v, j) => (
                <td key={j} className="px-2 py-1 border-b border-white/5">
                  {typeof v === "number" ? (v as number).toFixed(2) : String(v)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
