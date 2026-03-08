"use client";

import { useEffect, useState } from "react";
import { jobsApi, matchesApi, applicationsApi, resumesApi, type ScraperRun } from "@/lib/api";
import { motion } from "framer-motion";
import { Briefcase, Target, Send, Activity, FileText } from "lucide-react";
import PageContainer from "@/components/PageContainer";
import StatCard from "@/components/StatCard";
import GlassCard from "@/components/GlassCard";

export default function DashboardPage() {
  const [stats, setStats] = useState({ jobs: 0, matches: 0, apps: 0, resumes: 0 });
  const [runs, setRuns] = useState<ScraperRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [jobs, matches, apps, resumes, scraperRuns] = await Promise.all([
          jobsApi.list("?limit=1").catch(() => ({ total: 0 })),
          matchesApi.list("?status_filter=PENDING_APPROVAL&limit=1").catch(() => ({ total: 0 })),
          applicationsApi.list("?limit=1").catch(() => ({ total: 0 })),
          resumesApi.list("?limit=1").catch(() => ({ total: 0 })),
          jobsApi.scraperRuns(10).catch(() => []),
        ]);
        setStats({
          jobs: (jobs as { total: number })?.total || 0,
          matches: (matches as { total: number })?.total || 0,
          apps: (apps as { total: number })?.total || 0,
          resumes: (resumes as { total: number })?.total || 0,
        });
        setRuns((scraperRuns as ScraperRun[]) || []);
      } catch {
        // API may not be running yet
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const statCards = [
    { label: "Jobs Found", value: stats.jobs, icon: Briefcase, delay: 0 },
    { label: "Pending Matches", value: stats.matches, icon: Target, delay: 0.1 },
    { label: "Applications Sent", value: stats.apps, icon: Send, delay: 0.2 },
    { label: "Resumes", value: stats.resumes, icon: FileText, delay: 0.3 },
  ];

  return (
    <PageContainer>
      <header className="mb-12">
        <motion.h1 
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} 
          className="page-title"
        >
          Dashboard
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="text-[#a39f98] max-w-2xl"
        >
          Your highly-targeted automation campaign performance at a glance.
        </motion.p>
      </header>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[#06b6d4]" />
        </div>
      ) : (
        <>
          {/* Elegant Stat Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {statCards.map((card) => (
              <StatCard key={card.label} {...card} />
            ))}
          </div>

          {/* Scraper Health Activity Feed */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
          >
            <GlassCard hoverEffect={false}>
              <div className="flex items-center justify-between mb-8 border-b border-white/5 pb-5">
                <h2 className="text-xl font-semibold tracking-wide text-white">Scraper Health</h2>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#0a0a0f] border border-white/5">
                  <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_10px_#22c55e]" />
                  <span className="text-xs uppercase tracking-widest font-semibold text-[#a39f98]">System Active</span>
                </div>
              </div>

              {runs.length === 0 ? (
                <p className="text-center text-[#a39f98] py-12 text-sm font-medium">No recent activity detected.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse min-w-[700px]">
                    <thead>
                      <tr className="border-b border-white/5 text-xs uppercase tracking-widest text-[#a39f98]">
                        <th className="font-semibold py-3 px-4">Provider</th>
                        <th className="font-semibold py-3 px-4">Status</th>
                        <th className="font-semibold py-3 px-4 text-center">Jobs Analyzed</th>
                        <th className="font-semibold py-3 px-4 text-center">New Opportunities</th>
                        <th className="font-semibold py-3 px-4 text-right">Duration</th>
                        <th className="font-semibold py-3 px-4 text-right">Time</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {runs.map((run) => (
                        <tr key={run.id} className="hover:bg-white/[0.02] transition-colors group">
                          <td className="py-4 px-4">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-[#0a0a0f] border border-white/5 group-hover:border-[#06b6d4]/20 transition-colors">
                                {run.status === "SUCCESS" ? (
                                  <Activity size={14} className="text-[#06b6d4]" />
                                ) : (
                                  <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                                )}
                              </div>
                              <span className="text-sm font-medium text-white">{run.provider}</span>
                            </div>
                          </td>
                          <td className="py-4 px-4">
                            <span className={`badge ${run.status === "SUCCESS" ? "badge-success" : "badge-error"}`}>
                              {run.status}
                            </span>
                          </td>
                          <td className="py-4 px-4 text-center text-sm text-white/80">{run.jobs_found}</td>
                          <td className="py-4 px-4 text-center text-sm text-white/80 font-medium">{run.jobs_new}</td>
                          <td className="py-4 px-4 text-right text-sm text-white/50">{run.duration_seconds?.toFixed(1)}s</td>
                          <td className="py-4 px-4 text-right text-xs uppercase tracking-widest text-[#a39f98]">
                            {run.started_at ? new Date(run.started_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : "N/A"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </GlassCard>
          </motion.div>
        </>
      )}
    </PageContainer>
  );
}
