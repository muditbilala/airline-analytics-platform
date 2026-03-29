import { useMemo } from "react";
import type { HeatmapCell } from "../../api/analytics";
import ChartWrapper from "./ChartWrapper";

interface Props {
  data: HeatmapCell[] | null;
  loading: boolean;
}

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

function getColor(rate: number, min: number, max: number): string {
  const t = max === min ? 0 : (rate - min) / (max - min);
  // navy -> accent orange
  const r = Math.round(10 + t * (232 - 10));
  const g = Math.round(25 + t * (93 - 25));
  const b = Math.round(47 + t * (58 - 47));
  return `rgb(${r},${g},${b})`;
}

export default function HeatmapChart({ data, loading }: Props) {
  const { grid, min, max } = useMemo(() => {
    if (!data || data.length === 0) return { grid: new Map<string, number>(), min: 0, max: 1 };
    const g = new Map<string, number>();
    let mn = Infinity;
    let mx = -Infinity;
    for (const cell of data) {
      const key = `${cell.day_of_week}-${cell.hour}`;
      g.set(key, cell.delay_rate);
      if (cell.delay_rate < mn) mn = cell.delay_rate;
      if (cell.delay_rate > mx) mx = cell.delay_rate;
    }
    return { grid: g, min: mn, max: mx };
  }, [data]);

  return (
    <ChartWrapper title="Delay Heatmap (Day x Hour)" loading={loading}>
      <div className="overflow-x-auto">
        <div className="min-w-[640px]">
          {/* Hour labels */}
          <div className="flex ml-12 mb-1">
            {HOURS.map((h) => (
              <div
                key={h}
                className="flex-1 text-center text-[10px] text-text-secondary"
              >
                {h % 3 === 0 ? `${h}` : ""}
              </div>
            ))}
          </div>

          {/* Grid rows */}
          {DAYS.map((day, di) => (
            <div key={day} className="flex items-center mb-[2px]">
              <div className="w-12 text-xs text-text-secondary text-right pr-2 shrink-0">
                {day}
              </div>
              <div className="flex flex-1 gap-[2px]">
                {HOURS.map((h) => {
                  const rate = grid.get(`${di}-${h}`) ?? 0;
                  return (
                    <div
                      key={h}
                      className="flex-1 aspect-square rounded-sm cursor-default transition-transform hover:scale-125 hover:z-10"
                      style={{ backgroundColor: getColor(rate, min, max) }}
                      title={`${day} ${h}:00 — ${rate.toFixed(1)}% delay`}
                    />
                  );
                })}
              </div>
            </div>
          ))}

          {/* Legend */}
          <div className="flex items-center justify-end mt-3 gap-2 text-[10px] text-text-secondary">
            <span>Low</span>
            <div className="flex gap-0">
              {Array.from({ length: 8 }, (_, i) => (
                <div
                  key={i}
                  className="w-4 h-3 rounded-sm"
                  style={{ backgroundColor: getColor(min + (i / 7) * (max - min), min, max) }}
                />
              ))}
            </div>
            <span>High</span>
          </div>
        </div>
      </div>
    </ChartWrapper>
  );
}
