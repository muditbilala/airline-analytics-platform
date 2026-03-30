import { motion } from "framer-motion";
import { useRef, useState } from "react";
import HourlyDelayChart from "../components/charts/HourlyDelayChart";
import CarrierRankChart from "../components/charts/CarrierRankChart";
import DelayCauseChart from "../components/charts/DelayCauseChart";
import MonthlyTrendChart from "../components/charts/MonthlyTrendChart";
import { useDashboardData } from "../hooks/useAnalytics";

const _rawPbi = import.meta.env.VITE_POWERBI_EMBED_URL;
const POWERBI_URL: string | undefined =
  typeof _rawPbi === "string" && _rawPbi.trim().length > 0
    ? _rawPbi.trim()
    : undefined;

export default function Dashboard() {
  const { hourly, carriers, causes, trends, loading, error } =
    useDashboardData();
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [pbiLoading, setPbiLoading] = useState(true);

  const handleFullscreen = () => {
    if (iframeRef.current) {
      iframeRef.current.requestFullscreen?.();
    }
  };

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
            <div className="relative">
              {/* Header bar */}
              <div className="flex items-center justify-between px-5 py-3 border-b border-white/10 bg-navy-lighter/40">
                <div className="flex items-center gap-2">
                  {/* Power BI logo icon */}
                  <svg className="w-5 h-5 text-yellow-400" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="2" y="14" width="4" height="8" rx="1" />
                    <rect x="8" y="9" width="4" height="13" rx="1" />
                    <rect x="14" y="4" width="4" height="18" rx="1" />
                    <rect x="20" y="2" width="2" height="20" rx="1" opacity="0.5" />
                  </svg>
                  <span className="text-text-bright font-semibold text-sm">
                    Power BI · Flight Operations Intelligence Suite
                  </span>
                  <span className="text-xs text-text-secondary bg-white/5 px-2 py-0.5 rounded-full">
                    Live Report
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleFullscreen}
                    title="Fullscreen"
                    className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-bright transition-colors px-3 py-1.5 rounded-lg hover:bg-white/10"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
                    </svg>
                    Fullscreen
                  </button>
                  <a
                    href={POWERBI_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    title="Open in new tab"
                    className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-accent transition-colors px-3 py-1.5 rounded-lg hover:bg-white/10"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                    </svg>
                    Open
                  </a>
                </div>
              </div>

              {/* Loading spinner overlay */}
              {pbiLoading && (
                <div className="absolute inset-0 top-[49px] flex flex-col items-center justify-center bg-navy/80 backdrop-blur-sm z-10">
                  <div className="animate-spin w-10 h-10 border-2 border-accent border-t-transparent rounded-full mb-4" />
                  <p className="text-text-secondary text-sm">Loading Power BI report…</p>
                </div>
              )}

              <iframe
                ref={iframeRef}
                title="Power BI Dashboard — Flight Operations Intelligence Suite"
                src={POWERBI_URL}
                className="w-full border-0 block"
                style={{ height: "85vh", minHeight: 620 }}
                allowFullScreen
                allow="fullscreen"
                onLoad={() => setPbiLoading(false)}
              />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-24 px-4 text-center">
              <div className="w-20 h-20 rounded-2xl bg-navy-lighter/50 flex items-center justify-center mb-6">
                <svg className="w-10 h-10 text-yellow-400/60" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="2" y="14" width="4" height="8" rx="1" />
                  <rect x="8" y="9" width="4" height="13" rx="1" />
                  <rect x="14" y="4" width="4" height="18" rx="1" />
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
                environment variable to embed your published Power BI report here.
              </p>
              <div className="text-left bg-navy-lighter/40 rounded-xl px-5 py-4 text-sm text-text-secondary max-w-md">
                <p className="font-medium text-text-primary mb-2">How to embed:</p>
                <ol className="list-decimal list-inside space-y-1">
                  <li>Publish your report to Power BI Service</li>
                  <li>File → Embed report → Publish to web</li>
                  <li>Copy the embed URL</li>
                  <li>Add <code className="text-accent font-mono text-xs">VITE_POWERBI_EMBED_URL</code> to Vercel env vars</li>
                  <li>Redeploy</li>
                </ol>
              </div>
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
