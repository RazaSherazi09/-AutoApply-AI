import { Check, X } from "lucide-react";
import GlassCard from "./GlassCard";
import { Match } from "@/lib/api";
import { motion } from "framer-motion";

interface MatchCardProps {
  match: any; // Using any for now to map the exact flat structure discovered in page.tsx
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}

export default function MatchCard({ match, onApprove, onReject }: MatchCardProps) {
  const overallScore = Math.round((match.final_score || 0) * 100);
  
  const progressBars = [
    { label: "Semantic", value: (match.semantic_score || 0) * 100 },
    { label: "Skills", value: (match.skill_score || 0) * 100 },
    { label: "Title", value: (match.title_score || 0) * 100 },
    { label: "Location", value: (match.location_score || 0) * 100 }
  ];

  return (
    <GlassCard className="flex flex-col p-6 overflow-hidden">
      <div className="flex justify-between items-start mb-6 border-b border-white/5 pb-4">
        <div>
          <h3 className="text-lg font-semibold text-white mb-1 line-clamp-1">{match.job_title}</h3>
          <p className="text-sm text-[#a39f98]">{match.job_company}</p>
        </div>
        <div className="flex flex-col items-end flex-shrink-0 ml-4">
          <span className="text-3xl font-light text-white leading-none mb-1">
            {overallScore}<span className="text-lg text-[#06b6d4]">%</span>
          </span>
          <span className="text-[10px] uppercase font-semibold text-[#a39f98] tracking-widest">Match</span>
        </div>
      </div>

      <div className="space-y-4 mb-8 flex-1">
        {progressBars.map((bar) => (
          <div key={bar.label}>
            <div className="flex justify-between items-end mb-1.5">
              <span className="text-xs font-medium text-[#a39f98]">{bar.label}</span>
              <span className="text-xs text-white">{Math.round(bar.value)}%</span>
            </div>
            <div className="score-bar h-1.5">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${bar.value}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
                className="score-bar-fill" 
              />
            </div>
          </div>
        ))}
      </div>

      {match.status === "PENDING_APPROVAL" && (
        <div className="grid grid-cols-2 gap-3 mt-auto">
          <button 
            onClick={() => onApprove(match.id)}
            className="flex items-center justify-center gap-2 py-2.5 bg-green-500/10 text-green-400 border border-green-500/20 rounded-lg hover:bg-green-500/20 transition-colors text-sm font-medium"
          >
            <Check size={16} /> Approve
          </button>
          <button 
            onClick={() => onReject(match.id)}
            className="flex items-center justify-center gap-2 py-2.5 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg hover:bg-red-500/20 transition-colors text-sm font-medium"
          >
            <X size={16} /> Reject
          </button>
        </div>
      )}
      
      {match.status !== "PENDING_APPROVAL" && (
        <div className="mt-auto text-center py-2.5 rounded-lg border border-white/5 bg-white/5">
          <span className={`text-sm font-medium ${match.status === 'APPROVED' ? 'text-green-400' : 'text-red-400'}`}>
            {match.status}
          </span>
        </div>
      )}
    </GlassCard>
  );
}
