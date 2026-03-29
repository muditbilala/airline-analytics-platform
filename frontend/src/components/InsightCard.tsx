import { motion } from "framer-motion";

interface InsightCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  index: number;
}

export default function InsightCard({ title, description, icon, index }: InsightCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.5, delay: index * 0.08 }}
      className="group glass-card glow-border p-6 hover:bg-navy-light/90 transition-all duration-300 cursor-default"
    >
      <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center text-accent mb-4 group-hover:bg-accent/20 group-hover:scale-110 transition-all duration-300">
        {icon}
      </div>
      <h3 className="text-text-bright font-semibold text-base leading-snug mb-2 group-hover:text-accent transition-colors duration-300">
        {title}
      </h3>
      <p className="text-text-secondary text-sm leading-relaxed">
        {description}
      </p>
    </motion.div>
  );
}
