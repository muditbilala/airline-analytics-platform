import { useEffect, useState, useRef } from "react";
import { motion, useInView } from "framer-motion";

interface KPICardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  suffix?: string;
  prefix?: string;
  decimals?: number;
  color?: string;
}

function useCountUp(end: number, duration: number, decimals: number, inView: boolean) {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (!inView) return;
    let startTime: number | null = null;
    let raf: number;

    const animate = (ts: number) => {
      if (!startTime) startTime = ts;
      const progress = Math.min((ts - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(parseFloat((eased * end).toFixed(decimals)));
      if (progress < 1) raf = requestAnimationFrame(animate);
    };

    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, [end, duration, decimals, inView]);

  return current;
}

export default function KPICard({
  icon,
  label,
  value,
  suffix = "",
  prefix = "",
  decimals = 0,
  color = "accent",
}: KPICardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });
  const displayValue = useCountUp(value, 1800, decimals, inView);

  const colorMap: Record<string, string> = {
    accent: "from-accent/20 to-accent/5",
    success: "from-success/20 to-success/5",
    warning: "from-warning/20 to-warning/5",
    danger: "from-danger/20 to-danger/5",
  };

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.5 }}
      className="glass-card glow-border p-6 hover:scale-[1.02] transition-transform duration-300"
    >
      <div
        className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorMap[color] ?? colorMap.accent} flex items-center justify-center mb-4`}
      >
        {icon}
      </div>
      <p className="text-text-secondary text-sm font-medium mb-1">{label}</p>
      <p className="text-3xl font-bold text-text-bright font-mono">
        {prefix}
        {decimals > 0 ? displayValue.toFixed(decimals) : displayValue.toLocaleString()}
        {suffix}
      </p>
    </motion.div>
  );
}
