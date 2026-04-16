import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  delay?: number;
}

export default function StatCard({ label, value, icon: Icon, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.25, 0, 0, 1] }}
    >
      <div className="relative border border-[var(--border)] p-6 md:p-8 hover:border-[var(--border-hover)] transition-[border-color] duration-150 group">
        {/* Accent top bar */}
        <div className="absolute top-0 left-0 h-[2px] w-12 bg-[var(--accent)] opacity-60 group-hover:opacity-100 group-hover:w-16 transition-all duration-150" />
        
        <div className="flex items-center gap-3 mb-6">
          <Icon size={18} strokeWidth={1.5} className="text-[var(--muted-fg)] group-hover:text-[var(--accent)] transition-colors duration-150" />
          <span className="text-[var(--muted-fg)] uppercase tracking-[0.2em] text-[10px] font-bold" style={{ fontFamily: 'var(--font-mono)' }}>{label}</span>
        </div>
        
        <p className="text-5xl md:text-6xl font-bold tracking-tighter text-[var(--foreground)] leading-none" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.06em' }}>
          {value}
        </p>
      </div>
    </motion.div>
  );
}
