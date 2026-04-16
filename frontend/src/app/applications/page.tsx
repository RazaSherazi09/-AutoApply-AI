"use client";

import { useEffect, useState } from "react";
import { applicationsApi, type Application } from "@/lib/api";
import { motion } from "framer-motion";
import { Send, CheckCircle2, Clock, XCircle, AlertCircle, RefreshCw } from "lucide-react";
import PageContainer from "@/components/PageContainer";

export default function ApplicationsPage() {
  const [apps, setApps] = useState<Application[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  async function loadApps() {
    setLoading(true);
    try {
      const data = await applicationsApi.list("?limit=50");
      setApps(data.items);
      setTotal(data.total);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadApps(); }, []);

  const handleRetry = async (id: number) => {
    try {
      await applicationsApi.retry(id);
      await loadApps();
    } catch { }
  };

  const statusConfig: Record<string, { icon: any; color: string; label: string }> = {
    PENDING: { icon: Clock, color: "text-[var(--warning)]", label: "Queued" },
    SENT: { icon: Send, color: "text-[var(--accent)]", label: "Transmitted" },
    SUBMITTED: { icon: CheckCircle2, color: "text-[var(--success)]", label: "Submitted" },
    FAILED: { icon: XCircle, color: "text-[var(--error)]", label: "Failed" },
    MANUAL_REVIEW: { icon: AlertCircle, color: "text-[var(--warning)]", label: "Manual review" },
  };

  const getRelativeTime = (dateStr: string) => {
    const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
    const diffDays = Math.round((new Date().getTime() - new Date(dateStr).getTime()) / (1000 * 60 * 60 * 24));
    const diffHours = Math.round((new Date().getTime() - new Date(dateStr).getTime()) / (1000 * 60 * 60));
    const diffMins = Math.round((new Date().getTime() - new Date(dateStr).getTime()) / (1000 * 60));
    
    if (diffMins < 60) return rtf.format(-diffMins, 'minute');
    if (diffHours < 24) return rtf.format(-diffHours, 'hour');
    if (diffDays === 0) return 'today';
    return rtf.format(-diffDays, 'day');
  };

  return (
    <PageContainer>
      <header className="mb-16">
        <motion.h1 
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} 
          className="page-title mb-2"
        >
          Applications
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="text-[var(--muted-fg)] text-lg"
        >
          Tracking {total} deliveries.
        </motion.p>
      </header>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[var(--accent)]" />
        </div>
      ) : apps.length === 0 ? (
        <div className="text-center py-20 border border-[var(--border)]">
          <p className="text-2xl font-bold text-[var(--foreground)] tracking-tight mb-2" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>No applications yet.</p>
          <p className="text-sm text-[var(--muted-fg)] font-mono uppercase tracking-wider">Applications will appear as they deploy</p>
        </div>
      ) : (
        <div className="relative border-l-2 border-[var(--border)] ml-4 md:ml-6 pl-8 space-y-0">
          {apps.map((app, i) => {
            const cfg = statusConfig[app.status] || { icon: AlertCircle, color: "text-[var(--muted-fg)]", label: "Unknown" };
            const Icon = cfg.icon;
            
            return (
              <motion.div
                key={app.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05, duration: 0.5, ease: [0.25, 0, 0, 1] }}
                className="relative group pb-8"
              >
                {/* Timeline Dot */}
                <div className="absolute -left-[41px] top-6 w-4 h-4 bg-[var(--background)] border-2 border-[var(--border)] group-hover:border-[var(--accent)] transition-colors flex items-center justify-center">
                  <div className={`w-1.5 h-1.5 ${cfg.color === 'text-[var(--accent)]' ? 'bg-[var(--accent)]' : cfg.color === 'text-[var(--success)]' ? 'bg-[var(--success)]' : cfg.color === 'text-[var(--error)]' ? 'bg-[var(--error)]' : 'bg-[var(--warning)]'}`} />
                </div>

                <div className="border border-[var(--border)] hover:border-[var(--border-hover)] transition-[border-color] duration-150 p-6 md:p-8">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                    
                    <div>
                      <h3 className="text-lg md:text-xl font-bold text-[var(--foreground)] mb-2 group-hover:text-[var(--accent)] transition-colors tracking-tight" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>
                        Match #{app.match_id}
                      </h3>
                      <div className="flex items-center gap-3 text-sm">
                        <span className={cfg.color}>{cfg.label}</span>
                        <span className="text-[var(--border)]">—</span>
                        <span className="text-[var(--muted-fg)] font-mono uppercase tracking-wider text-xs">{app.method} / {app.handler_type}</span>
                      </div>
                    </div>

                    <div className="flex flex-col md:items-end gap-2">
                      <span className="text-sm text-[var(--muted-fg)] font-mono">
                        {getRelativeTime(app.created_at)}
                      </span>
                      
                      {(app.status === "FAILED" || app.status === "MANUAL_REVIEW") && (
                        <button 
                          onClick={() => handleRetry(app.id)} 
                          className="btn-ghost text-xs flex items-center gap-2 py-1 px-2"
                        >
                          <RefreshCw size={12} strokeWidth={1.5} /> Retry
                        </button>
                      )}
                    </div>
                  </div>

                  {app.error_log && (
                    <div className="mt-4 p-4 border border-[var(--error)]/20 text-[var(--error)] font-mono text-xs md:text-sm overflow-x-auto">
                      <div className="flex items-center gap-2 mb-2 label-upper text-[var(--error)]">
                        <AlertCircle size={12} strokeWidth={1.5} /> Exception
                      </div>
                      {app.error_log}
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </PageContainer>
  );
}
