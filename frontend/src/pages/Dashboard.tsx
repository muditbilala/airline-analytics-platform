import { motion } from "framer-motion";
import HourlyDelayChart from "../components/charts/HourlyDelayChart";
import CarrierRankChart from "../components/charts/CarrierRankChart";
import DelayCauseChart from "../components/charts/DelayCauseChart";
import MonthlyTrendChart from "../components/charts/MonthlyTrendChart";
import { useDashboardData } from "../hooks/useAnalytics";

const POWERBI_URL = import.meta.env.VITE_POWERBI_EMBED_URL as
  | string
  | undefined;

export default function Dashboard() {
  const { hourly, carriers, causes, trends, loading, error } =
    useDashboardData();

  return (
    <div className="pt-20 pb-16 px-4">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <h1 className="text-3xl sm:text-4xl font-bold text-text-bright mb-2">
            Dashboard
          </h1>
          <p className="text-text-secondary text-lg">
            Power BI embedded dashboard with live analytics
          </p>
        </motion.div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-danger/10 border border-danger/20 text-danger text-sm">
            {error}
          </div>
        )}

        {/* Power BI Embed */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="glass-card overflow-hidden mb-8"
        >
          {POWERBI_URL ? (
            <iframe
              title="Power BI Dashboard"
              src={POWERBI_URL}
              className="w-full border-0"
              style={{ height: "70vh", minHeight: 500 }}
              allowFullScreen
            />
          ) : (
            <div className="flex flex-col items-center justify-center py-24 px-4 text-center">
              <div className="w-20 h-20 rounded-2xl bg-navy-lighter/50 flex items-center justify-center mb-6">
                <svg
                  className="w-10 h-10 text-text-secondary"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"
                  />
                </svg>
              </div>
              <h3 className="text-text-bright font-semibold text-xl mb-2">
                Power BI Dashboard
              </h3>
              <p className="text-text-secondary max-w-md mb-4">
                Set the{" "}
                <code className="text-accent font-mono text-sm bg-accent/10 px-2 py-0.5 rounded">
                  VITE_POWERBI_EMBED_URL
                </code>{" "}
                environment variable to embed your Power BI report here.
              </p>
              <p className="text-text-secondary text-sm">
                Add it to a{" "}
                <code className="text-text-primary font-mono text-xs">
                  .env
                </code>{" "}
                file in the frontend root.
              </p>
            </div>
          )}
        </motion.div>

        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-6"
        >
          <h2 className="text-2xl font-bold text-text-bright mb-1">
            Live Analytics
          </h2>
          <p className="text-text-secondary text-sm">
            Real-time charts from the backend API
          </p>
        </motion.div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="chart-card">
            <MonthlyTrendChart data={trends} loading={loading} />
          </div>
          <div className="chart-card">
            <DelayCauseChart data={causes} loading={loading} />
          </div>
        </div>

        <div className="mb-6 chart-card">
          <CarrierRankChart data={carriers} loading={loading} />
        </div>

        <div className="chart-card">
          <HourlyDelayChart data={hourly} loading={loading} />
        </div>
      </div>
    </div>
  );
}
