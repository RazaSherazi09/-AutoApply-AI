"use client";

import { useEffect, useState } from "react";
import { jobsApi, matchesApi, applicationsApi, resumesApi, settingsApi, type ScraperRun } from "@/lib/api";
import { motion } from "framer-motion";
import { Briefcase, Target, Send, Activity, FileText, Clock, Play, Pause } from "lucide-react";
import PageContainer from "@/components/PageContainer";
import StatCard from "@/components/StatCard";
import GlassCard from "@/components/GlassCard";

export default function DashboardPage() {
  const [stats, setStats] = useState({ jobs: 0, matches: 0, apps: 0, resumes: 0 });
  const [runs, setRuns] = useState<ScraperRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [nextScrapeTime, setNextScrapeTime] = useState<string>("Calculating...");
  const [intervalMins, setIntervalMins] = useState(60);
  const [isPaused, setIsPaused] = useState(false);
  const [toggling, setToggling] = useState(false);

  // Timer Effect
  useEffect(() => {
    const updateTimer = () => {
      const lastScrape = localStorage.getItem('lastScrapeTime');
      const now = Date.now();
      
      let nextTime = now + (intervalMins * 60 * 1000);
      if (lastScrape) {
        const last = parseInt(lastScrape);
        const elapsed = now - last;
        const totalIntervalMs = intervalMins * 60 * 1000;
        
        if (elapsed >= totalIntervalMs) {
          // If past due, fake a recent reset for the timer visual or assume it just ran
          localStorage.setItem('lastScrapeTime', now.toString());
          nextTime = now + totalIntervalMs;
        } else {
          nextTime = last + totalIntervalMs;
        }
      } else {
        localStorage.setItem('lastScrapeTime', now.toString());
      }

      const diff = nextTime - now;
      if (diff <= 0) {
         setNextScrapeTime("Running now...");
      } else {
         const m = Math.floor((diff / 1000) / 60);
         const s = Math.floor((diff / 1000) % 60);
         setNextScrapeTime(`${m}m ${s}s`);
      }
    };
    
    updateTimer();
    const intervalId = setInterval(updateTimer, 1000);
    return () => clearInterval(intervalId);
  }, [intervalMins]);

  useEffect(() => {
    async function load() {
      try {
        const [jobs, matches, apps, resumes, scraperRuns, config] = await Promise.all([
          jobsApi.list("?limit=1").catch(() => ({ total: 0 })),
          matchesApi.list("?status_filter=PENDING_APPROVAL&limit=1").catch(() => ({ total: 0 })),
          applicationsApi.list("?limit=1").catch(() => ({ total: 0 })),
          resumesApi.list("?limit=1").catch(() => ({ total: 0 })),
          jobsApi.scraperRuns(5).catch(() => []),
          settingsApi.getConfig().catch(() => ({ scrape_interval_minutes: "60" }))
        ]);
        
        if (config && (config as any).scrape_interval_minutes) {
           setIntervalMins(parseInt((config as any).scrape_interval_minutes));
        }
        if (config && (config as any).is_scraping_paused === "true") {
           setIsPaused(true);
        }
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

  const togglePause = async () => {
    setToggling(true);
    try {
      const newState = !isPaused;
      await settingsApi.updateConfig({ is_scraping_paused: newState ? "true" : "false" });
      setIsPaused(newState);
      if (!newState) {
         // Reset timer when unpausing
         localStorage.setItem('lastScrapeTime', Date.now().toString());
      }
    } catch {
      // ignore
    } finally {
      setToggling(false);
    }
  };

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
      
      {/* Synchronization Timer Banner */}
      <motion.div 
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
        className="mb-8 bg-[#0a0a0f] border border-white/5 rounded-2xl p-4 flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
           <div className="w-10 h-10 rounded-full bg-[#06b6d4]/10 border border-[#06b6d4]/20 flex items-center justify-center">
             <Clock size={18} className="text-[#06b6d4]" />
           </div>
           <div>
             <h3 className="text-white text-sm font-semibold tracking-wide">Synchronization Timer</h3>
             <p className="text-[#a39f98] text-xs">Interval set to {intervalMins} minutes</p>
           </div>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center gap-6">
           {/* Actions */}
           <div className="flex items-center gap-3 border-r border-white/10 pr-6">
              {isPaused ? (
                 <button 
                  onClick={togglePause} disabled={toggling}
                  className="bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/20 px-4 py-2 rounded-full flex items-center gap-2 text-xs font-semibold tracking-wide transition-colors"
                 >
                   <Play size={14} /> Resume Scrape
                 </button>
              ) : (
                 <button 
                  onClick={togglePause} disabled={toggling}
                  className="bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 px-4 py-2 rounded-full flex items-center gap-2 text-xs font-semibold tracking-wide transition-colors"
                 >
                   <Pause size={14} /> Stop Scrape
                 </button>
              )}
           </div>
           <div className="text-right">
             <p className="text-[#a39f98] text-[10px] uppercase tracking-widest font-bold mb-1">Next AI Scrape In</p>
             <p className={`text-xl font-mono font-light tracking-tight ${isPaused ? 'text-red-400' : 'text-[#06b6d4]'}`}>
                {isPaused ? "PAUSED" : nextScrapeTime}
             </p>
           </div>
        </div>
      </motion.div>

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
                <h2 className="text-xl font-semibold tracking-wide text-white">Latest Execution Batch</h2>
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
