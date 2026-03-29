import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Suspense } from "react";
import Globe from "../components/Globe";
import ParticleField from "../components/ParticleField";

export default function Landing() {
  return (
    <div className="relative min-h-screen flex flex-col">
      {/* Hero Section */}
      <section className="relative flex-1 flex items-center justify-center min-h-screen overflow-hidden">
        {/* Particle Background */}
        <ParticleField />

        {/* 3D Globe Background */}
        <div className="absolute inset-0 z-[1]">
          <Suspense
            fallback={
              <div className="w-full h-full bg-navy flex items-center justify-center">
                <div className="w-16 h-16 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
              </div>
            }
          >
            <Globe />
          </Suspense>
        </div>

        {/* Gradient overlays */}
        <div className="absolute inset-0 z-[2] bg-gradient-to-b from-navy/70 via-navy/30 to-navy pointer-events-none" />
        <div className="absolute inset-0 z-[2] bg-gradient-to-r from-navy/50 via-transparent to-navy/50 pointer-events-none" />

        {/* Content */}
        <div className="relative z-10 text-center px-4 max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 border border-accent/20 text-accent text-sm font-medium mb-8">
              <span className="relative w-2 h-2 rounded-full bg-accent">
                <span className="absolute inset-0 rounded-full bg-accent animate-ping" />
              </span>
              Powered by 2.76M+ Flight Records
            </div>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.15, ease: "easeOut" }}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-text-bright leading-tight mb-6"
          >
            Airline Operations{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent via-accent-light to-warning gradient-text-animated">
              Intelligence
            </span>{" "}
            Platform
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
            className="text-text-secondary text-lg sm:text-xl max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Analyzing 2.76M+ flights to uncover operational inefficiencies.
            Explore delay patterns, carrier rankings, and AI-driven insights
            through interactive visualizations.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.45, ease: "easeOut" }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <Link
              to="/insights"
              className="px-8 py-3.5 bg-accent hover:bg-accent-light text-white font-semibold rounded-xl transition-all duration-300 hover:shadow-lg hover:shadow-accent/25 hover:-translate-y-0.5"
            >
              Explore Insights
            </Link>
            <Link
              to="/dashboard"
              className="px-8 py-3.5 bg-white/5 hover:bg-white/10 text-text-primary font-semibold rounded-xl border border-white/10 hover:border-white/20 transition-all duration-300 hover:-translate-y-0.5"
            >
              View Dashboard
            </Link>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5, duration: 1 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 flex flex-col items-center gap-2"
        >
          <span className="text-text-secondary text-xs tracking-widest uppercase">
            Scroll
          </span>
          <div className="scroll-indicator">
            <svg
              className="w-5 h-5 text-text-secondary"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M19 14l-7 7m0 0l-7-7"
              />
            </svg>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-text-bright mb-4">
              What You Can Explore
            </h2>
            <p className="text-text-secondary max-w-xl mx-auto">
              From real-time metrics to AI-powered questions, dive into every
              dimension of airline operations.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                title: "Interactive Analytics",
                desc: "Explore delay patterns by hour, carrier, cause, and season with rich visualizations powered by Recharts.",
                icon: (
                  <svg
                    className="w-6 h-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
                    />
                  </svg>
                ),
                link: "/insights",
              },
              {
                title: "Power BI Dashboard",
                desc: "Full-featured embedded dashboard with cross-filtering and drill-down capabilities for advanced analysis.",
                icon: (
                  <svg
                    className="w-6 h-6"
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
                ),
                link: "/dashboard",
              },
              {
                title: "AI Chat Assistant",
                desc: "Ask natural language questions about flight data and get instant insights with dynamic charts and tables.",
                icon: (
                  <svg
                    className="w-6 h-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
                    />
                  </svg>
                ),
                link: "/chatbot",
              },
            ].map((card, i) => (
              <motion.div
                key={card.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
              >
                <Link
                  to={card.link}
                  className="glass-card glow-border block p-8 hover:bg-navy-light/90 transition-all duration-300 group h-full insight-shine"
                >
                  <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center text-accent mb-5 group-hover:bg-accent/20 group-hover:scale-110 transition-all duration-300">
                    {card.icon}
                  </div>
                  <h3 className="text-text-bright font-semibold text-lg mb-2 group-hover:text-accent transition-colors">
                    {card.title}
                  </h3>
                  <p className="text-text-secondary text-sm leading-relaxed">
                    {card.desc}
                  </p>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Section Divider */}
        <div className="section-divider max-w-4xl mx-auto mt-24" />
      </section>

      {/* Stats Preview */}
      <section className="pb-24 px-4">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-text-bright mb-4">
              By the Numbers
            </h2>
            <p className="text-text-secondary max-w-xl mx-auto">
              Key metrics from our analysis of U.S. domestic flight operations
            </p>
          </motion.div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Flights Analyzed", value: "2.76M+", accent: true },
              { label: "On-Time Rate", value: "78.9%", accent: false },
              { label: "Airlines Covered", value: "16+", accent: false },
              { label: "Airports", value: "370+", accent: true },
            ].map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                className="glass-card p-6 text-center"
              >
                <p
                  className={`text-3xl sm:text-4xl font-bold font-mono mb-2 ${
                    stat.accent ? "text-accent" : "text-success"
                  }`}
                >
                  {stat.value}
                </p>
                <p className="text-text-secondary text-sm">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
