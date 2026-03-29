import { motion } from "framer-motion";
import KPICard from "../components/KPICard";
import InsightCard from "../components/InsightCard";
import HourlyDelayChart from "../components/charts/HourlyDelayChart";
import CarrierRankChart from "../components/charts/CarrierRankChart";
import DelayCauseChart from "../components/charts/DelayCauseChart";
import MonthlyTrendChart from "../components/charts/MonthlyTrendChart";
import HeatmapChart from "../components/charts/HeatmapChart";
import { useAnalytics } from "../hooks/useAnalytics";

const INSIGHTS = [
  {
    title: "Evening flights (5-9 PM) show 30%+ higher delay rates",
    description:
      "Delays compound throughout the day as aircraft rotations accumulate cascading delays. Morning flights departing before 8 AM have the best on-time performance.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    title: "Late aircraft cascading causes 39% of all delay minutes",
    description:
      "The single biggest delay driver is not weather or air traffic, but late-arriving aircraft from prior flights. This operational inefficiency ripples through airline schedules.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
      </svg>
    ),
  },
  {
    title: "Spirit & JetBlue lead delays; Republic & SkyWest lead on-time",
    description:
      "Budget carriers consistently rank worst for delays, while regional operators maintaining tight hub-and-spoke schedules deliver superior punctuality.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
  },
  {
    title: "ATL handles 135K flights with below-average delay rates",
    description:
      "Hartsfield-Jackson Atlanta, the world's busiest airport, manages massive throughput while maintaining competitive delay performance through operational excellence.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 0h.008v.008h-.008V7.5z" />
      </svg>
    ),
  },
  {
    title: "Friday and Sunday are the worst days to fly",
    description:
      "Weekend bookend days see 15-20% higher delay rates than midweek. Tuesday and Wednesday consistently offer the best travel experience with lowest delay probability.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
      </svg>
    ),
  },
  {
    title: "Carrier issues, not weather, drive most delays",
    description:
      "Contrary to popular belief, carrier-controllable factors (maintenance, crew, operations) account for more delay minutes than weather across the dataset.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
      </svg>
    ),
  },
];

export default function Insights() {
  const { overview, hourly, carriers, causes, trends, heatmap, loading, error } =
    useAnalytics();

  const kpiFlights = overview?.total_flights ?? 2760000;
  const kpiOnTime = overview?.on_time_pct ?? 78.9;
  const kpiDelay = overview?.delay_pct ?? 21.1;
  const kpiCancel = overview?.cancel_pct ?? 1.5;

  return (
    <div className="pt-20 pb-16 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-10"
        >
          <h1 className="text-3xl sm:text-4xl font-bold text-text-bright mb-2">
            Flight Delay Insights
          </h1>
          <p className="text-text-secondary text-lg">
            Comprehensive analytics across 2.76M+ U.S. domestic flights
          </p>
        </motion.div>

        {error && (
          <div className="mb-8 p-4 rounded-xl bg-danger/10 border border-danger/20 text-danger text-sm">
            {error}
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          <KPICard
            icon={
              <svg className="w-6 h-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
            }
            label="Total Flights"
            value={kpiFlights}
            color="accent"
          />
          <KPICard
            icon={
              <svg className="w-6 h-6 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            label="On-Time Rate"
            value={kpiOnTime}
            suffix="%"
            decimals={1}
            color="success"
          />
          <KPICard
            icon={
              <svg className="w-6 h-6 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            label="Delay Rate"
            value={kpiDelay}
            suffix="%"
            decimals={1}
            color="warning"
          />
          <KPICard
            icon={
              <svg className="w-6 h-6 text-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
            }
            label="Cancelled"
            value={kpiCancel}
            suffix="%"
            decimals={1}
            color="danger"
          />
        </div>

        {/* Section Divider */}
        <div className="section-divider mb-12" />

        {/* Key Findings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <h2 className="text-2xl sm:text-3xl font-bold text-text-bright mb-2">
            Key Findings
          </h2>
          <p className="text-text-secondary">
            Data-driven insights from our analysis
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-16">
          {INSIGHTS.map((insight, i) => (
            <InsightCard
              key={insight.title}
              title={insight.title}
              description={insight.description}
              icon={insight.icon}
              index={i}
            />
          ))}
        </div>

        {/* Section Divider */}
        <div className="section-divider mb-12" />

        {/* Charts Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <h2 className="text-2xl sm:text-3xl font-bold text-text-bright mb-2">
            Deep-Dive Analytics
          </h2>
          <p className="text-text-secondary">
            Interactive charts powered by live data
          </p>
        </motion.div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="chart-card">
            <HourlyDelayChart data={hourly} loading={loading} />
          </div>
          <div className="chart-card">
            <DelayCauseChart data={causes} loading={loading} />
          </div>
        </div>

        <div className="mb-6 chart-card">
          <CarrierRankChart data={carriers} loading={loading} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="chart-card">
            <MonthlyTrendChart data={trends} loading={loading} />
          </div>
          <div className="chart-card">
            <HeatmapChart data={heatmap} loading={loading} />
          </div>
        </div>
      </div>
    </div>
  );
}
