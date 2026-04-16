"use client";

import { useEffect, useState } from "react";
import { jobsApi, type Job } from "@/lib/api";
import { motion } from "framer-motion";
import { Search, RefreshCw, ArrowRight } from "lucide-react";
import PageContainer from "@/components/PageContainer";
import JobCard from "@/components/JobCard";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("All");
  const [remoteOnly, setRemoteOnly] = useState(false);

  const [scraping, setScraping] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [scrapeMsg, setScrapeMsg] = useState("");

  async function loadJobs() {
    setLoading(true);
    try {
      let params = `?limit=50&remote_only=${remoteOnly}`;
      if (search) params += `&search=${encodeURIComponent(search)}`;
      if (source !== "All") params += `&source=${source}`;
      const data = await jobsApi.list(params);
      setJobs(data.items);
      setTotal(data.total);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadJobs(); }, [search, source, remoteOnly]);

  const handleScrape = async () => {
    setScraping(true);
    setScrapeMsg("");
    try {
      await jobsApi.scrape();
      localStorage.setItem('lastScrapeTime', Date.now().toString());
      setScrapeMsg("Intelligence gathering initiated.");
      setTimeout(loadJobs, 2500);
      setTimeout(loadJobs, 6000);
      setTimeout(loadJobs, 12000);
    } catch (err: unknown) {
      setScrapeMsg(`Error: ${err instanceof Error ? err.message : "Scrape failed"}`);
    } finally {
      setScraping(false);
    }
  };

  const handleClear = async () => {
    if (!confirm("Are you sure you want to clear all scraped jobs and matches?")) return;
    setClearing(true);
    setScrapeMsg("");
    try {
      await jobsApi.clear();
      setScrapeMsg("Database wiped. Ready for fresh data.");
      setJobs([]);
      setTotal(0);
    } catch (err: unknown) {
      setScrapeMsg(`Error: ${err instanceof Error ? err.message : "Clear failed"}`);
    } finally {
      setClearing(false);
    }
  };

  return (
    <PageContainer>
      <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <motion.h1 
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} 
            className="page-title mb-2"
          >
            Job Board
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
            className="text-[var(--muted-fg)] text-lg"
          >
            Curated opportunities matching your profile.
          </motion.p>
        </div>
        
        <motion.div 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          className="flex items-center gap-3 border border-[var(--border)] px-5 py-3"
        >
          <span className="w-2 h-[2px] bg-[var(--accent)]" />
          <span className="text-sm font-bold text-[var(--foreground)] font-mono">{total}</span>
          <span className="label-upper">Available</span>
        </motion.div>
      </header>

      {/* Filters */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
        className="flex flex-col md:flex-row items-stretch gap-0 mb-10 w-full border border-[var(--border)]"
      >
        <div className="flex-1 flex items-center gap-3 px-5 py-3 border-b md:border-b-0 md:border-r border-[var(--border)] focus-within:bg-[var(--muted)]/30">
          <Search size={16} strokeWidth={1.5} className="text-[var(--muted-fg)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent border-none outline-none text-[var(--foreground)] w-full placeholder:text-[var(--muted-fg)] text-sm"
            placeholder="Search by title, role..."
          />
        </div>
        
        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="bg-transparent px-5 py-3 text-[var(--foreground)] appearance-none outline-none cursor-pointer border-b md:border-b-0 md:border-r border-[var(--border)] text-sm font-medium min-w-[140px]"
        >
          <option value="All">All Sources</option>
          <option value="adzuna">Adzuna</option>
          <option value="greenhouse">Greenhouse</option>
          <option value="lever">Lever</option>
          <option value="workday">Workday</option>
        </select>
        
        <label className="flex items-center gap-3 cursor-pointer px-5 py-3 hover:bg-[var(--muted)]/30 transition-colors text-sm">
          <input
            type="checkbox"
            checked={remoteOnly}
            onChange={(e) => setRemoteOnly(e.target.checked)}
            className="w-4 h-4 accent-[var(--accent)]"
          />
          <span className="text-[var(--foreground)] font-medium uppercase tracking-wider text-xs">Remote</span>
        </label>
      </motion.div>

      {/* Listings */}
      <div className="mb-16">
        {loading ? (
          <div className="flex justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[var(--accent)]" />
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-20 border border-[var(--border)]">
            <p className="text-2xl font-bold text-[var(--foreground)] tracking-tight mb-2" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>No opportunities found.</p>
            <p className="text-sm text-[var(--muted-fg)] font-mono uppercase tracking-wider">Adjust your filters</p>
          </div>
        ) : (
          <div className="space-y-0 divide-y divide-[var(--border)] border border-[var(--border)]">
            {jobs.map((job, i) => (
              <motion.div
                key={job.id}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * Math.min(i, 10) }}
              >
                <JobCard 
                  job={job}
                  statusBadge={
                    <>
                      <span className="badge badge-neutral">{job.source}</span>
                      {job.job_type && <span className="badge badge-neutral">{job.job_type}</span>}
                    </>
                  }
                  onApply={() => window.open(job.url, "_blank")}
                />
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Scrape Section */}
      <motion.div 
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}
      >
        <div className="border-t border-[var(--border)] pt-12">
          <div className="max-w-2xl">
            <div className="flex items-center gap-3 mb-4">
              <RefreshCw size={18} strokeWidth={1.5} className="text-[var(--accent)]" />
              <h2 className="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)]" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>
                AI Scraping
              </h2>
            </div>
            <p className="text-sm text-[var(--muted-fg)] mb-8 leading-relaxed max-w-xl">
              Initiate a fully automated scrape. The engine extracts data from your resume, combines with your profile preferences, and scans all integrated platforms.
            </p>
            
            <div className="flex flex-col sm:flex-row items-start gap-4">
              <button
                onClick={handleScrape}
                disabled={scraping || clearing}
                className="btn-secondary px-8"
              >
                {scraping ? "Scraping..." : "Initialize Scrape"}
              </button>
              
              <button
                onClick={handleClear}
                disabled={scraping || clearing}
                className="btn-danger px-6"
              >
                {clearing ? "Purging..." : "Clear All"}
              </button>
            </div>
            {scrapeMsg && (
              <p className="mt-4 text-sm text-[var(--accent)] font-mono tracking-wide">
                {scrapeMsg}
              </p>
            )}
          </div>
        </div>
      </motion.div>
    </PageContainer>
  );
}
