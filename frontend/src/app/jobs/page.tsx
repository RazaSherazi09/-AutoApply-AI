"use client";

import { useEffect, useState } from "react";
import { jobsApi, type Job } from "@/lib/api";
import { motion } from "framer-motion";
import { Search, RefreshCw } from "lucide-react";
import PageContainer from "@/components/PageContainer";
import JobCard from "@/components/JobCard";
import GlassCard from "@/components/GlassCard";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("All");
  const [remoteOnly, setRemoteOnly] = useState(false);

  // Scrape
  const [scraping, setScraping] = useState(false);
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
      setScrapeMsg("Intelligence gathering initiated using your AI Profile.");
      // Poll a few times to auto-load incoming jobs
      setTimeout(loadJobs, 2500);
      setTimeout(loadJobs, 6000);
      setTimeout(loadJobs, 12000);
    } catch (err: unknown) {
      setScrapeMsg(`Error: ${err instanceof Error ? err.message : "Scrape failed"}`);
    } finally {
      setScraping(false);
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
            className="text-[#a39f98]"
          >
            Curated opportunities matching your sophisticated profile.
          </motion.p>
        </div>
        
        <motion.div 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          className="flex items-center gap-3 bg-[#0a0a0f] border border-white/5 rounded-full p-1.5 pr-4"
        >
          <div className="w-8 h-8 rounded-full bg-[#0f0f23] border border-white/10 flex items-center justify-center">
            <span className="w-2 h-2 rounded-full bg-[#06b6d4] animate-pulse shadow-[0_0_8px_#06b6d4]" />
          </div>
          <span className="text-sm font-medium text-white">{total} Available curated roles</span>
        </motion.div>
      </header>

      {/* Filters Top Bar */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
        className="flex flex-col md:flex-row items-center gap-4 mb-10 w-full"
      >
        <div className="flex-1 flex items-center gap-3 bg-[#0a0a0f] border border-white/5 rounded-full px-5 py-3 w-full focus-within:border-[#06b6d4]/40 transition-colors">
          <Search size={18} className="text-[#a39f98]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent border-none outline-none text-white w-full placeholder:text-[#a39f98]"
            placeholder="Search by title, role..."
          />
        </div>
        
        <div className="flex items-center gap-4 w-full md:w-auto">
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="bg-[#0a0a0f] border border-white/5 rounded-full px-5 py-3 text-white appearance-none outline-none focus:border-[#06b6d4]/40 cursor-pointer min-w-[140px]"
          >
            <option value="All">All Sources</option>
            <option value="adzuna">Adzuna</option>
            <option value="greenhouse">Greenhouse</option>
            <option value="lever">Lever</option>
            <option value="workday">Workday</option>
          </select>
          
          <label className="flex items-center gap-3 cursor-pointer bg-[#0a0a0f] border border-white/5 rounded-full px-5 py-3 hover:border-white/20 transition-colors">
            <input
              type="checkbox"
              checked={remoteOnly}
              onChange={(e) => setRemoteOnly(e.target.checked)}
              className="w-4 h-4 accent-[#06b6d4]"
            />
            <span className="text-sm text-white font-medium">Remote Only</span>
          </label>
        </div>
      </motion.div>

      {/* Clean Premium Listings */}
      <div className="mb-16">
        {loading ? (
          <div className="flex justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[#06b6d4]" />
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-20 border border-white/5 rounded-2xl bg-[#0a0a0f]/50">
            <p className="text-[#a39f98] font-sans text-lg mb-2 font-medium">No opportunities found.</p>
            <p className="text-sm text-[#a39f98]/60">Adjust your sophisticated filtering parameters.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {jobs.map((job, i) => (
              <motion.div
                key={job.id}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * Math.min(i, 10) }}
              >
                <JobCard 
                  job={job}
                  statusBadge={
                    <>
                      <span className="badge badge-neutral bg-white/[0.02]">{job.source}</span>
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

      {/* AI Scrape Area - Minimal Layout */}
      <motion.div 
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}
      >
        <GlassCard hoverEffect={false}>
          <div className="max-w-3xl">
            <h2 className="text-xl font-semibold tracking-wide text-white mb-4 flex items-center gap-3">
              <RefreshCw size={20} className="text-[#06b6d4]" /> AI Intelligence Gathering
            </h2>
            <p className="text-sm text-[#a39f98] mb-8 leading-relaxed max-w-xl">
              Initiate a fully automated scrape. The neural engine will extract Job Titles and Skills from your Resume, combine them with your Career Profile preferences (Country & Workplace Type), and scan across all integrated platforms instantly.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <button
                onClick={handleScrape}
                disabled={scraping}
                className="btn-secondary whitespace-nowrap px-8"
              >
                {scraping ? "Acquiring Intelligence..." : "Initialize AI Scrape"}
              </button>
            </div>
            {scrapeMsg && (
              <p className="mt-4 text-sm text-[#06b6d4] font-medium tracking-wide">
                {scrapeMsg}
              </p>
            )}
          </div>
        </GlassCard>
      </motion.div>
    </PageContainer>
  );
}
