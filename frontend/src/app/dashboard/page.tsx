"use client";

import { useEffect, useState } from "react";
import { jobsApi, matchesApi, applicationsApi, resumesApi, settingsApi, type ScraperRun } from "@/lib/api";
import { motion } from "framer-motion";
import { Briefcase, Target, Send, Activity, FileText, Clock, Play, Pause } from "lucide-react";
import PageContainer from "@/components/PageContainer";
import StatCard from "@/components/StatCard";

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
    { label: "Applications", value: stats.apps, icon: Send, delay: 0.2 },
    { label: "Resumes", value: stats.resumes, icon: FileText, delay: 0.3 },
  ];

  return (
    <PageContainer>
      <header className="mb-16">
        <motion.h1 
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} 
          className="page-title"
        >
          Dashboard
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="text-[var(--muted-fg)] text-lg max-w-xl"
        >
          Campaign performance at a glance.
        </motion.p>
      </header>
      
      {/* Synchronization Timer */}
      <motion.div 
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
        className="mb-10 border border-[var(--border)] p-5 md:p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6"
      >
        <div className="flex items-center gap-4">
           <Clock size={20} strokeWidth={1.5} className="text-[var(--accent)]" />
           <div>
             <h3 className="text-[var(--foreground)] text-sm font-bold uppercase tracking-[0.1em]" style={{ fontFamily: 'var(--font-mono)' }}>Sync Timer</h3>
             <p className="text-[var(--muted-fg)] text-xs font-mono">Interval: {intervalMins} minutes</p>
           </div>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center gap-6">
           <div className="flex items-center gap-3">
              {isPaused ? (
                 <button 
                  onClick={togglePause} disabled={toggling}
                  className="btn-success text-xs py-2 px-5 flex items-center gap-2"
                 >
                   <Play size={12} strokeWidth={1.5} /> Resume
                 </button>
              ) : (
                 <button 
                  onClick={togglePause} disabled={toggling}
                  className="btn-danger text-xs py-2 px-5 flex items-center gap-2"
                 >
                   <Pause size={12} strokeWidth={1.5} /> Pause
                 </button>
              )}
           </div>
           <div className="border-l border-[var(--border)] pl-6">
             <p className="label-upper mb-1">Next Scrape</p>
             <p className={`text-2xl font-bold tracking-tighter ${isPaused ? 'text-[var(--error)]' : 'text-[var(--accent)]'}`} style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.06em' }}>
                {isPaused ? "PAUSED" : nextScrapeTime}
             </p>
           </div>
        </div>
      </motion.div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[var(--accent)]" />
        </div>
      ) : (
        <>
          {/* Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {statCards.map((card) => (
              <StatCard key={card.label} {...card} />
            ))}
          </div>

          {/* Scraper Runs Table */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
          >
            <div className="border border-[var(--border)]">
              <div className="flex items-center justify-between p-6 md:p-8 border-b border-[var(--border)]">
                <h2 className="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)]" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>
                  Latest Executions
                </h2>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-[2px] bg-[var(--success)]" />
                  <span className="label-upper">Active</span>
                </div>
              </div>

              {runs.length === 0 ? (
                <p className="text-center text-[var(--muted-fg)] py-12 text-sm font-mono uppercase tracking-wider">No recent activity.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse min-w-[700px]">
                    <thead>
                      <tr className="border-b border-[var(--border)]">
                        <th className="label-upper py-4 px-6">Provider</th>
                        <th className="label-upper py-4 px-6">Status</th>
                        <th className="label-upper py-4 px-6 text-center">Analyzed</th>
                        <th className="label-upper py-4 px-6 text-center">New</th>
                        <th className="label-upper py-4 px-6 text-right">Duration</th>
                        <th className="label-upper py-4 px-6 text-right">Time</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--border)]">
                      {runs.map((run) => (
                        <tr key={run.id} className="hover:bg-[var(--muted)]/50 transition-colors group">
                          <td className="py-4 px-6">
                            <div className="flex items-center gap-3">
                              <Activity size={14} strokeWidth={1.5} className={run.status === "SUCCESS" ? "text-[var(--accent)]" : "text-[var(--error)]"} />
                              <span className="text-sm font-medium text-[var(--foreground)]">{run.provider}</span>
                            </div>
                          </td>
                          <td className="py-4 px-6">
                            <span className={`badge ${run.status === "SUCCESS" ? "badge-success" : "badge-error"}`}>
                              {run.status}
                            </span>
                          </td>
                          <td className="py-4 px-6 text-center text-sm text-[var(--foreground)] font-mono">{run.jobs_found}</td>
                          <td className="py-4 px-6 text-center text-sm text-[var(--foreground)] font-mono font-bold">{run.jobs_new}</td>
                          <td className="py-4 px-6 text-right text-sm text-[var(--muted-fg)] font-mono">{run.duration_seconds?.toFixed(1)}s</td>
                          <td className="py-4 px-6 text-right label-upper">
                            {run.started_at ? new Date(run.started_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : "N/A"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </PageContainer>
  );
}
