import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";
import GlassCard from "./GlassCard";

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
      transition={{ duration: 0.5, delay, ease: [0.16, 1, 0.3, 1] }}
    >
      <GlassCard className="h-full flex flex-col group p-6 overflow-hidden">
        {/* Gradient Top Border */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#06b6d4] to-[#8b5cf6] opacity-50 group-hover:opacity-100 transition-opacity" />
        
        {/* Faint Background Icon */}
        <div className="absolute top-4 right-4 opacity-5 group-hover:opacity-10 transition-opacity duration-500">
          <Icon size={100} className="text-[#06b6d4] -mr-4 -mt-4 transform group-hover:scale-110 transition-transform duration-500" />
        </div>
        
        <div className="flex items-center gap-4 mb-6">
          <div className="w-10 h-10 rounded-full bg-[#0f0f23] border border-white/5 flex items-center justify-center text-[#06b6d4] group-hover:text-[#8b5cf6] transition-colors shadow-inner">
            <Icon size={18} />
          </div>
          <h3 className="text-sm font-medium tracking-wide text-[#a39f98]">{label}</h3>
        </div>
        
        <div className="mt-auto z-10">
          <p className="text-4xl font-semibold tracking-tight text-white mb-2 font-sans">
            {value}
          </p>
        </div>
      </GlassCard>
    </motion.div>
  );
}
