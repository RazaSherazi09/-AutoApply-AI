"use client";

import { useEffect, useState } from "react";
import { applicationsApi, type Application } from "@/lib/api";
import { motion } from "framer-motion";
import { Send, CheckCircle2, Clock, XCircle, AlertCircle, RefreshCw } from "lucide-react";
import PageContainer from "@/components/PageContainer";
import GlassCard from "@/components/GlassCard";

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
    PENDING: { icon: Clock, color: "text-amber-400", label: "Queued for deployment" },
    SENT: { icon: Send, color: "text-[#06b6d4]", label: "Transmitted to parser" },
    SUBMITTED: { icon: CheckCircle2, color: "text-green-500", label: "Submission verified" },
    FAILED: { icon: XCircle, color: "text-red-500", label: "Encountered failure" },
    MANUAL_REVIEW: { icon: AlertCircle, color: "text-amber-500", label: "Requires manual bypass" },
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
          Application Log
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="text-[#a39f98]"
        >
          Real-time feed tracking exactly {total} payload deliveries.
        </motion.p>
      </header>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[#06b6d4]" />
        </div>
      ) : apps.length === 0 ? (
        <div className="text-center py-20 border border-white/5 rounded-2xl bg-[#0a0a0f]/50">
          <p className="text-[#a39f98] font-sans text-lg mb-2 font-medium">The ledger is empty.</p>
          <p className="text-sm text-[#a39f98]/60">Automated applications will appear here as they deploy.</p>
        </div>
      ) : (
        <div className="relative border-l border-white/10 ml-6 pl-8 space-y-12">
          {apps.map((app, i) => {
            const cfg = statusConfig[app.status] || { icon: AlertCircle, color: "text-[#a39f98]", label: "Unknown status" };
            const Icon = cfg.icon;
            
            return (
              <motion.div
                key={app.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                className="relative group"
              >
                {/* Timeline Dot */}
                <div className="absolute -left-[45px] top-1.5 w-6 h-6 rounded-full bg-[#0a0a0f] border border-white/20 flex items-center justify-center transition-colors group-hover:border-[#06b6d4]/50 group-hover:shadow-[0_0_10px_rgba(6,182,212,0.5)]">
                  <Icon size={12} className={cfg.color} />
                </div>

                <GlassCard className="p-6 md:p-8">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                    
                    <div className="flex items-start gap-4">
                      <div>
                        <h3 className="text-xl font-medium text-white mb-2 group-hover:text-[#06b6d4] transition-colors">
                          Application initiated for Match #{app.match_id}
                        </h3>
                        <div className="flex items-center gap-3 text-sm">
                          <span className={cfg.color}>{cfg.label}</span>
                          <span className="text-white/20">•</span>
                          <span className="text-[#a39f98] capitalize">{app.method} / {app.handler_type}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col md:items-end gap-2">
                      <span className="text-sm text-[#a39f98]/70 font-mono">
                        {getRelativeTime(app.created_at)}
                      </span>
                      
                      {(app.status === "FAILED" || app.status === "MANUAL_REVIEW") && (
                        <button 
                          onClick={() => handleRetry(app.id)} 
                          className="bg-white/5 hover:bg-white/10 text-white border border-white/10 hover:border-white/30 py-2 px-4 rounded-full text-xs font-medium flex items-center gap-2 transition-colors mt-2"
                        >
                          <RefreshCw size={12} /> Retry Payload
                        </button>
                      )}
                    </div>
                  </div>

                  {app.error_log && (
                    <div className="mt-4 p-4 rounded-xl bg-[#0a0a0f] border border-red-500/10 text-red-400 font-mono text-xs md:text-sm overflow-x-auto shadow-inner">
                      <div className="flex items-center gap-2 mb-2 text-[10px] uppercase font-bold tracking-widest text-red-500/70">
                        <AlertCircle size={14} /> System Exception
                      </div>
                      {app.error_log}
                    </div>
                  )}
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      )}
    </PageContainer>
  );
}
