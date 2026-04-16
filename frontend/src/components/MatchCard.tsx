import { Check, X } from "lucide-react";
import { Match } from "@/lib/api";
import { motion } from "framer-motion";

interface MatchCardProps {
  match: any;
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
    <div className="border border-[var(--border)] hover:border-[var(--border-hover)] transition-[border-color] duration-150 p-6 flex flex-col overflow-hidden relative">
      {/* Accent top bar */}
      <div className="absolute top-0 left-0 h-[2px] w-12 bg-[var(--accent)]" />

      <div className="flex justify-between items-start mb-6 pb-4 border-b border-[var(--border)]">
        <div className="min-w-0 flex-1 mr-4">
          <h3 className="text-lg font-bold text-[var(--foreground)] mb-1 line-clamp-1 tracking-tight" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>
            {match.job_title}
          </h3>
          <p className="text-sm text-[var(--muted-fg)] uppercase tracking-[0.1em]" style={{ fontFamily: 'var(--font-mono)' }}>
            {match.job_company}
          </p>
        </div>
        <div className="flex flex-col items-end flex-shrink-0">
          <span className="text-4xl font-bold text-[var(--foreground)] leading-none tracking-tighter" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.06em' }}>
            {overallScore}<span className="text-lg text-[var(--accent)] font-bold">%</span>
          </span>
          <span className="text-[10px] uppercase font-bold text-[var(--muted-fg)] tracking-[0.2em] mt-1" style={{ fontFamily: 'var(--font-mono)' }}>Match</span>
        </div>
      </div>

      <div className="space-y-4 mb-8 flex-1">
        {progressBars.map((bar) => (
          <div key={bar.label}>
            <div className="flex justify-between items-end mb-1.5">
              <span className="label-upper">{bar.label}</span>
              <span className="text-xs font-mono text-[var(--foreground)] tracking-tight">{Math.round(bar.value)}%</span>
            </div>
            <div className="score-bar h-[3px]">
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
            className="btn-success flex items-center justify-center gap-2 py-2.5 text-sm"
          >
            <Check size={14} strokeWidth={1.5} /> Approve
          </button>
          <button 
            onClick={() => onReject(match.id)}
            className="btn-danger flex items-center justify-center gap-2 py-2.5 text-sm"
          >
            <X size={14} strokeWidth={1.5} /> Reject
          </button>
        </div>
      )}
      
      {match.status !== "PENDING_APPROVAL" && (
        <div className="mt-auto text-center py-2.5 border border-[var(--border)]">
          <span className={`text-sm font-bold uppercase tracking-[0.1em] ${match.status === 'APPROVED' ? 'text-[var(--success)]' : 'text-[var(--error)]'}`} style={{ fontFamily: 'var(--font-mono)' }}>
            {match.status}
          </span>
        </div>
      )}
    </div>
  );
}
