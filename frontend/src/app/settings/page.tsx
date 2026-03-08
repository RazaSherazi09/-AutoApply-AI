"use client";

import { useEffect, useState } from "react";
import { settingsApi } from "@/lib/api";
import { motion } from "framer-motion";
import { Settings2, ShieldCheck, Activity } from "lucide-react";
import PageContainer from "@/components/PageContainer";
import GlassCard from "@/components/GlassCard";

export default function SettingsPage() {
  const [scrapeInterval, setScrapeInterval] = useState(60);
  const [matchThreshold, setMatchThreshold] = useState(0.65);
  const [maxApps, setMaxApps] = useState(25);
  const [keywords, setKeywords] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const config = await settingsApi.getConfig();
        if (config.scrape_interval_minutes)
          setScrapeInterval(parseInt(config.scrape_interval_minutes));
        if (config.match_threshold)
          setMatchThreshold(parseFloat(config.match_threshold));
        if (config.max_applications_per_day)
          setMaxApps(parseInt(config.max_applications_per_day));
        if (config.required_keywords) setKeywords(config.required_keywords);
      } catch {
        // ignore — will use defaults
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMsg("");
    try {
      await settingsApi.updateConfig({
        scrape_interval_minutes: String(scrapeInterval),
        match_threshold: String(matchThreshold),
        max_applications_per_day: String(maxApps),
        required_keywords: keywords,
      });
      setMsg("✅ System configuration preserved securely.");
      setTimeout(() => setMsg(""), 3000);
    } catch (err: unknown) {
      setMsg(`❌ ${err instanceof Error ? err.message : "Save failed"}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <PageContainer>
      <header className="mb-16">
        <motion.h1 
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} 
          className="page-title mb-2"
        >
          System Configuration
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="text-[#a39f98] max-w-2xl"
        >
          Configure the underlying operational parameters of your automation agent.
        </motion.p>
      </header>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[#06b6d4]" />
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-[1fr_350px] gap-8 items-start">
          
          <motion.form 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            onSubmit={handleSave} 
          >
            <GlassCard hoverEffect={false} className="p-8 md:p-12">
              <div className="flex items-center gap-3 mb-10 pb-6 border-b border-white/5">
                <Settings2 className="text-[#06b6d4]" size={24} />
                <h2 className="text-2xl font-semibold tracking-wide text-white">Execution Parameters</h2>
              </div>

              <div className="space-y-12">
                
                {/* Match Threshold */}
                <div className="bg-[#0a0a0f] p-6 rounded-2xl border border-white/5 shadow-inner">
                  <div className="flex items-center justify-between mb-4">
                    <label className="text-[10px] font-bold uppercase tracking-widest text-[#06b6d4]">
                      Calibration Threshold
                    </label>
                    <span className="text-3xl font-light font-sans text-white tracking-tight">
                      {(matchThreshold * 100).toFixed(0)}<span className="text-lg text-[#a39f98] font-normal">%</span>
                    </span>
                  </div>
                  <input
                    type="range"
                    value={matchThreshold}
                    onChange={(e) => setMatchThreshold(Number(e.target.value))}
                    className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-[#06b6d4]"
                    style={{
                      background: `linear-gradient(to right, #06b6d4 0%, #8b5cf6 ${matchThreshold * 100}%, rgba(255,255,255,0.05) ${matchThreshold * 100}%, rgba(255,255,255,0.05) 100%)`,
                    }}
                    min={0}
                    max={1}
                    step={0.05}
                  />
                  <div className="flex justify-between text-[10px] uppercase font-semibold tracking-widest text-[#a39f98] mt-4">
                    <span>Broad Match (0%)</span>
                    <span>Exact Profile Only (100%)</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {/* Scrape Interval */}
                  <div className="bg-[#0a0a0f] p-6 rounded-2xl border border-white/5 shadow-inner">
                    <label className="block text-[10px] font-bold uppercase tracking-widest text-[#a39f98] mb-4">
                      Synchronization Interval
                    </label>
                    <div className="flex items-end gap-3 border-b border-white/10 pb-2 focus-within:border-[#06b6d4]/50 transition-colors">
                      <input
                        type="number"
                        value={scrapeInterval}
                        onChange={(e) => setScrapeInterval(Number(e.target.value))}
                        className="bg-transparent border-none outline-none text-3xl font-light w-full text-white"
                        min={5}
                      />
                      <span className="text-sm text-[#a39f98] pb-1">min</span>
                    </div>
                  </div>

                  {/* Max Applications */}
                  <div className="bg-[#0a0a0f] p-6 rounded-2xl border border-white/5 shadow-inner">
                    <label className="block text-[10px] font-bold uppercase tracking-widest text-[#a39f98] mb-4">
                      Daily Activity Limit
                    </label>
                    <div className="flex items-end gap-3 border-b border-white/10 pb-2 focus-within:border-[#8b5cf6]/50 transition-colors">
                      <input
                        type="number"
                        value={maxApps}
                        onChange={(e) => setMaxApps(Number(e.target.value))}
                        className="bg-transparent border-none outline-none text-3xl font-light w-full text-white"
                        min={1}
                        max={100}
                      />
                      <span className="text-sm text-[#a39f98] pb-1">apps</span>
                    </div>
                  </div>
                </div>

                {/* Required Keywords */}
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#a39f98] mb-3 pl-1">
                    Strict Keywords Constraint
                  </label>
                  <input
                    type="text"
                    value={keywords}
                    onChange={(e) => setKeywords(e.target.value)}
                    className="input-field max-w-full"
                    placeholder="e.g. python, remote, senior..."
                  />
                  <p className="text-sm text-[#a39f98]/60 mt-3 font-medium pl-1">Opportunities lacking these keywords will be automatically discarded.</p>
                </div>

                {/* Footer Actions */}
                <div className="pt-8 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-6">
                  <div className="flex flex-col">
                     {msg && (
                      <motion.span 
                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                        className={`text-sm tracking-wide font-medium flex items-center gap-2 px-4 py-2 rounded-full border bg-[#0a0a0f] ${msg.includes("✅") ? "text-green-400 border-green-500/20" : "text-red-400 border-red-500/20"}`}
                      >
                        {msg}
                      </motion.span>
                     )}
                  </div>
                  
                  <button 
                    type="submit" 
                    disabled={saving} 
                    className="btn-primary w-full sm:w-auto min-w-[200px]"
                  >
                    {saving ? "Updating..." : "Enforce Parameters"}
                  </button>
                </div>

              </div>
            </GlassCard>
          </motion.form>

          {/* Info Sidebar */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="space-y-6"
          >
            <GlassCard hoverEffect={false} className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <ShieldCheck size={20} className="text-[#06b6d4]" />
                <h3 className="font-semibold text-lg text-white">Security Protocol</h3>
              </div>
              <p className="text-sm text-[#a39f98] leading-relaxed mb-6">
                Critical credentials, including SMTP protocols and cryptographic API keys, are rigorously isolated from the presentation layer.
              </p>
              <div className="bg-[#0a0a0f] border border-white/5 rounded-xl p-4 flex flex-col gap-2 shadow-inner">
                <span className="text-[10px] uppercase font-bold text-[#a39f98] tracking-widest">Environment File</span>
                <code className="text-[#8b5cf6] text-sm font-mono tracking-tight">.env (Local only)</code>
              </div>
            </GlassCard>

            <GlassCard hoverEffect={false} className="p-6">
              <div className="flex items-center gap-3 mb-6">
                <Activity size={20} className="text-[#06b6d4]" />
                <h3 className="font-semibold text-lg text-white">System Status</h3>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-4 border-b border-white/5 text-sm">
                  <span className="text-[#a39f98] font-medium">Background Sync</span>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_#22c55e]" />
                    <span className="text-green-400 font-semibold tracking-wide">Active</span>
                  </div>
                </div>
                <div className="flex items-center justify-between pb-4 border-b border-white/5 text-sm">
                  <span className="text-[#a39f98] font-medium">Matching Engine</span>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_#22c55e]" />
                    <span className="text-green-400 font-semibold tracking-wide">Nominal</span>
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-[#a39f98] font-medium">Webdriver Core</span>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#06b6d4] shadow-[0_0_8px_#06b6d4]" />
                    <span className="text-[#06b6d4] font-semibold tracking-wide">Ready</span>
                  </div>
                </div>
              </div>
            </GlassCard>
          </motion.div>
        </div>
      )}
    </PageContainer>
  );
}
