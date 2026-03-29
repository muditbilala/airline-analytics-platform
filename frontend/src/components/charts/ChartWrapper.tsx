import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface Props {
  title: string;
  loading: boolean;
  children: ReactNode;
}

export default function ChartWrapper({ title, loading, children }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.5 }}
      className="glass-card p-6"
    >
      <h3 className="text-text-bright font-semibold text-lg mb-4">{title}</h3>
      {loading ? (
        <div className="space-y-3">
          <div className="skeleton h-8 w-3/4" />
          <div className="skeleton h-64 w-full" />
        </div>
      ) : (
        children
      )}
    </motion.div>
  );
}
