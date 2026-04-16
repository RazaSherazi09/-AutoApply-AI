import { ReactNode } from "react";
import { Globe, MapPin, DollarSign, ArrowRight } from "lucide-react";
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
    <div className="border border-[var(--border)] hover:border-[var(--border-hover)] transition-[border-color] duration-150 p-6 md:p-8 flex flex-col xl:flex-row gap-6 justify-between items-start group">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-3 flex-wrap">
          <h3 className="text-xl md:text-2xl font-bold text-[var(--foreground)] group-hover:text-[var(--accent)] transition-colors duration-150 tracking-tight" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>
            {job.title}
          </h3>
          {statusBadge}
        </div>
        
        <p className="text-base text-[var(--muted-fg)] mb-4 font-medium flex flex-wrap items-center gap-3">
          <span className="text-[var(--foreground)]">{job.company}</span>
          <span className="text-[var(--border)]">—</span>
          <span className="flex items-center gap-1"><MapPin size={14} strokeWidth={1.5} /> {job.location || "Undisclosed"}</span>
          {(job.salary_min !== null || job.salary_max !== null) && (
            <>
              <span className="text-[var(--border)]">—</span>
              <span className="flex items-center gap-1 text-[var(--success)]">
                <DollarSign size={14} strokeWidth={1.5} /> 
                ${job.salary_min ? (job.salary_min / 1000).toFixed(0) + "k" : "?"} – ${job.salary_max ? (job.salary_max / 1000).toFixed(0) + "k" : "?"}
              </span>
            </>
          )}
        </p>

        <div className="flex flex-wrap gap-2 mb-4">
          {isRemote && (
            <span className="badge badge-primary flex items-center gap-1">
              <Globe size={12} strokeWidth={1.5} /> Remote
            </span>
          )}
          {skills.slice(0, 5).map((skill: string) => (
            <span key={skill} className="badge badge-neutral">
              {skill}
            </span>
          ))}
          {skills.length > 5 && (
            <span className="text-[10px] uppercase font-mono tracking-[0.2em] text-[var(--muted-fg)] self-center">
              +{skills.length - 5}
            </span>
          )}
        </div>
        
        <p className="text-sm text-[var(--muted-fg)] line-clamp-2 leading-relaxed max-w-2xl">
          {job.description?.replace(/<[^>]*>?/gm, '') || "No description provided."}
        </p>
      </div>

      {onApply && (
        <div className="xl:w-48 w-full flex-shrink-0 flex items-center xl:justify-end xl:mt-0 mt-2">
          <button 
            onClick={onApply}
            className="btn-primary whitespace-nowrap flex items-center gap-2"
          >
            Apply Now <ArrowRight size={16} strokeWidth={1.5} />
          </button>
        </div>
      )}
    </div>
  );
}
