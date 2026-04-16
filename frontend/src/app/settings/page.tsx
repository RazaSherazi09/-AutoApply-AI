"use client";

import { useEffect, useState } from "react";
import { settingsApi } from "@/lib/api";
import { motion } from "framer-motion";
import { Settings2, ShieldCheck, Activity } from "lucide-react";
import PageContainer from "@/components/PageContainer";

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
        // ignore
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
      setMsg("✅ Configuration saved.");
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
          Settings
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="text-[var(--muted-fg)] text-lg max-w-xl"
        >
          Operational parameters of your automation agent.
        </motion.p>
      </header>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[var(--accent)]" />
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-8 items-start">
          
          <motion.form 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5, ease: [0.25, 0, 0, 1] }}
            onSubmit={handleSave} 
          >
            <div className="border border-[var(--border)] p-8 md:p-12">
              <div className="flex items-center gap-3 mb-10 pb-6 border-b border-[var(--border)]">
                <Settings2 size={20} strokeWidth={1.5} className="text-[var(--accent)]" />
                <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-[var(--foreground)]" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>Parameters</h2>
              </div>

              <div className="space-y-12">
                
                {/* Match Threshold */}
                <div className="border border-[var(--border)] p-6 relative">
                  <div className="absolute top-0 left-0 h-[2px] w-12 bg-[var(--accent)]" />
                  <div className="flex items-center justify-between mb-4">
                    <label className="label-upper text-[var(--accent)]">
                      Match Threshold
                    </label>
                    <span className="text-4xl font-bold text-[var(--foreground)] tracking-tighter" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.06em' }}>
                      {(matchThreshold * 100).toFixed(0)}<span className="text-lg text-[var(--muted-fg)]">%</span>
                    </span>
                  </div>
                  <input
                    type="range"
                    value={matchThreshold}
                    onChange={(e) => setMatchThreshold(Number(e.target.value))}
                    className="w-full h-[3px] appearance-none cursor-pointer accent-[var(--accent)]"
                    style={{
                      background: `linear-gradient(to right, var(--accent) 0%, var(--accent) ${matchThreshold * 100}%, var(--border) ${matchThreshold * 100}%, var(--border) 100%)`,
                    }}
                    min={0}
                    max={1}
                    step={0.05}
                  />
                  <div className="flex justify-between label-upper mt-4 opacity-60">
                    <span>Broad (0%)</span>
                    <span>Exact (100%)</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {/* Scrape Interval */}
                  <div className="border border-[var(--border)] p-6 relative">
                    <div className="absolute top-0 left-0 h-[2px] w-8 bg-[var(--accent)]" />
                    <label className="label-upper block mb-4">
                      Sync Interval
                    </label>
                    <div className="flex items-end gap-3 border-b border-[var(--border)] pb-2 focus-within:border-[var(--accent)] transition-colors">
                      <input
                        type="number"
                        value={scrapeInterval}
                        onChange={(e) => setScrapeInterval(Number(e.target.value))}
                        className="bg-transparent border-none outline-none text-4xl font-bold w-full text-[var(--foreground)]"
                        style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.06em' }}
                        min={5}
                      />
                      <span className="text-sm text-[var(--muted-fg)] pb-1 font-mono">min</span>
                    </div>
                  </div>

                  {/* Max Applications */}
                  <div className="border border-[var(--border)] p-6 relative">
                    <div className="absolute top-0 left-0 h-[2px] w-8 bg-[var(--accent)]" />
                    <label className="label-upper block mb-4">
                      Daily Limit
                    </label>
                    <div className="flex items-end gap-3 border-b border-[var(--border)] pb-2 focus-within:border-[var(--accent)] transition-colors">
                      <input
                        type="number"
                        value={maxApps}
                        onChange={(e) => setMaxApps(Number(e.target.value))}
                        className="bg-transparent border-none outline-none text-4xl font-bold w-full text-[var(--foreground)]"
                        style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.06em' }}
                        min={1}
                        max={100}
                      />
                      <span className="text-sm text-[var(--muted-fg)] pb-1 font-mono">apps</span>
                    </div>
                  </div>
                </div>

                {/* Keywords */}
                <div>
                  <label className="label-upper block mb-3">
                    Required Keywords
                  </label>
                  <input
                    type="text"
                    value={keywords}
                    onChange={(e) => setKeywords(e.target.value)}
                    className="input-field"
                    placeholder="python, remote, senior..."
                  />
                  <p className="label-upper mt-3 opacity-60">Jobs without these keywords are discarded</p>
                </div>

                {/* Footer */}
                <div className="pt-8 border-t border-[var(--border)] flex flex-col sm:flex-row items-center justify-between gap-6">
                  <div>
                     {msg && (
                      <motion.span 
                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                        className={`text-sm font-mono tracking-wide ${msg.includes("✅") ? "text-[var(--success)]" : "text-[var(--error)]"}`}
                      >
                        {msg}
                      </motion.span>
                     )}
                  </div>
                  
                  <button 
                    type="submit" 
                    disabled={saving} 
                    className="btn-secondary w-full sm:w-auto px-10"
                  >
                    {saving ? "Saving..." : "Save Settings"}
                  </button>
                </div>

              </div>
            </div>
          </motion.form>

          {/* Sidebar */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.5, ease: [0.25, 0, 0, 1] }}
            className="space-y-6"
          >
            <div className="border border-[var(--border)] p-6">
              <div className="flex items-center gap-3 mb-6">
                <Activity size={18} strokeWidth={1.5} className="text-[var(--accent)]" />
                <h3 className="font-bold text-lg text-[var(--foreground)] tracking-tight" style={{ fontFamily: 'var(--font-display)' }}>Status</h3>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-4 border-b border-[var(--border)] text-sm">
                  <span className="text-[var(--muted-fg)]">Background Sync</span>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-[2px] bg-[var(--success)]" />
                    <span className="text-[var(--success)] font-bold uppercase tracking-wider text-xs font-mono">Active</span>
                  </div>
                </div>
                <div className="flex items-center justify-between pb-4 border-b border-[var(--border)] text-sm">
                  <span className="text-[var(--muted-fg)]">Match Engine</span>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-[2px] bg-[var(--success)]" />
                    <span className="text-[var(--success)] font-bold uppercase tracking-wider text-xs font-mono">Nominal</span>
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-[var(--muted-fg)]">Browser Core</span>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-[2px] bg-[var(--accent)]" />
                    <span className="text-[var(--accent)] font-bold uppercase tracking-wider text-xs font-mono">Ready</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </PageContainer>
  );
}
