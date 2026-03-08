import { ReactNode } from "react";
import { Globe, MapPin, DollarSign, Send } from "lucide-react";
import GlassCard from "./GlassCard";
import { Job } from "@/lib/api";

interface JobCardProps {
  job: Job;
  onApply?: () => void;
  statusBadge?: ReactNode;
}

export default function JobCard({ job, onApply, statusBadge }: JobCardProps) {
  const isRemote = job.remote_status?.toLowerCase() === "remote" || job.location?.toLowerCase().includes("remote");
  
  let skills: string[] = [];
  try {
    skills = JSON.parse(job.extracted_skills || "[]");
  } catch {
    skills = [];
  }

  return (
    <GlassCard className="flex flex-col xl:flex-row gap-6 justify-between items-start p-6 group">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-2 flex-wrap">
          <h3 className="text-xl font-semibold text-white group-hover:text-[#06b6d4] transition-colors truncate">
            {job.title}
          </h3>
          {statusBadge}
        </div>
        
        <p className="text-base text-[#a39f98] mb-4 font-medium flex flex-wrap items-center gap-2">
          <span className="text-white">{job.company}</span>
          <span className="text-white/20">•</span>
          <span className="flex items-center gap-1"><MapPin size={14} /> {job.location || "Undisclosed"}</span>
          {(job.salary_min !== null || job.salary_max !== null) && (
            <>
              <span className="text-white/20">•</span>
              <span className="flex items-center gap-1 text-green-400/80">
                <DollarSign size={14} /> 
                ${job.salary_min ? (job.salary_min / 1000).toFixed(0) + "k" : "?"} - ${job.salary_max ? (job.salary_max / 1000).toFixed(0) + "k" : "?"}
              </span>
            </>
          )}
        </p>

        <div className="flex flex-wrap gap-2 mb-4">
          {isRemote && (
            <span className="px-2.5 py-1 text-[10px] uppercase font-bold tracking-widest rounded border border-[#06b6d4]/30 text-[#06b6d4] bg-[#06b6d4]/5 flex items-center gap-1">
              <Globe size={12} /> Remote
            </span>
          )}
          {skills.slice(0, 5).map((skill: string) => (
            <span key={skill} className="px-2.5 py-1 text-[10px] uppercase font-semibold tracking-widest rounded text-[#a39f98] bg-white/5">
              {skill}
            </span>
          ))}
          {skills.length > 5 && (
            <span className="px-2.5 py-1 text-[10px] uppercase font-semibold tracking-widest rounded text-white/30 bg-transparent">
              +{skills.length - 5}
            </span>
          )}
        </div>
        
        <p className="text-sm text-[#a39f98]/80 line-clamp-2 leading-relaxed">
          {job.description?.replace(/<[^>]*>?/gm, '') || "No description provided."}
        </p>
      </div>

      {onApply && (
        <div className="xl:w-48 w-full flex-shrink-0 flex items-center xl:justify-end xl:mt-0 mt-2">
          <button 
            onClick={onApply}
            className="w-full xl:w-auto btn-primary whitespace-nowrap"
          >
            Apply Now <Send size={16} className="ml-1" />
          </button>
        </div>
      )}
    </GlassCard>
  );
}
