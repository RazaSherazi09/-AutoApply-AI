"use client";

import { useEffect, useState } from "react";
import { settingsApi } from "@/lib/api";
import { motion } from "framer-motion";
import { Compass, Sparkles, CheckCircle2 } from "lucide-react";
import PageContainer from "@/components/PageContainer";
import GlassCard from "@/components/GlassCard";

export default function PreferencesPage() {
  const [titles, setTitles] = useState("");
  const [locations, setLocations] = useState("");
  const [excluded, setExcluded] = useState("");
  const [minSalary, setMinSalary] = useState(0);
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [country, setCountry] = useState("Worldwide");
  const [workplaceType, setWorkplaceType] = useState("Any");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const pref = await settingsApi.getPreferences();
        const parseSafe = (raw: string) => {
          try { return JSON.parse(raw); } catch { return []; }
        };
        setTitles(parseSafe(pref.desired_titles || "[]").join("\n"));
        setLocations(parseSafe(pref.desired_locations || "[]").join("\n"));
        setExcluded(parseSafe(pref.excluded_companies || "[]").join("\n"));
        setMinSalary(pref.min_salary || 0);
        setRemoteOnly(pref.remote_only);
        setCountry(pref.country || "Worldwide");
        setWorkplaceType(pref.workplace_type || "Any");
      } catch { } finally { setLoading(false); }
    }
    load();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMsg("");
    try {
      await settingsApi.updatePreferences({
        desired_titles: titles.split("\n").map((t) => t.trim()).filter(Boolean),
        desired_locations: locations.split("\n").map((l) => l.trim()).filter(Boolean),
        excluded_companies: excluded.split("\n").map((c) => c.trim()).filter(Boolean),
        min_salary: minSalary > 0 ? minSalary : null,
        remote_only: remoteOnly,
        country: country,
        workplace_type: workplaceType,
      });
      setMsg("✅ Profile parameters successfully synchronized.");
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
          Targeting Preferences
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="text-[#a39f98] max-w-2xl"
        >
          Fine-tune the neural matching engine's alignment vectors. What opportunities do you seek?
        </motion.p>
      </header>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[#06b6d4]" />
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <form onSubmit={handleSave}>
            <GlassCard hoverEffect={false} className="max-w-4xl p-8 md:p-12">
              
              <div className="flex items-center gap-3 mb-10 pb-6 border-b border-white/5">
                <Compass className="text-[#06b6d4]" size={24} />
                <h2 className="text-2xl font-semibold tracking-wide text-white">Career Profile</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                
                {/* Left Column */}
                <div className="space-y-10">
                  <div>
                    <label className="block text-[10px] font-bold uppercase tracking-widest text-[#a39f98] mb-3 pl-1">
                      Desired Titles <span className="text-[#06b6d4]">*</span>
                    </label>
                    <textarea
                      value={titles}
                      onChange={(e) => setTitles(e.target.value)}
                      className="input-field min-h-[140px] resize-y font-medium text-sm leading-relaxed"
                      placeholder="Principal Software Engineer&#10;Head of Engineering&#10;Director of Technology"
                    />
                    <p className="text-[11px] text-[#a39f98]/60 mt-2 font-medium pl-1">Separate each title with a new line.</p>
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold uppercase tracking-widest text-[#a39f98] mb-3 pl-1">
                      Target Geographies
                    </label>
                    <textarea
                      value={locations}
                      onChange={(e) => setLocations(e.target.value)}
                      className="input-field min-h-[140px] resize-y font-medium text-sm leading-relaxed"
                      placeholder="San Francisco, CA&#10;London, UK&#10;New York City"
                    />
                  </div>
                </div>

                {/* Right Column */}
                <div className="space-y-10">
                  <div>
                    <label className="block text-[10px] font-bold uppercase tracking-widest text-[#a39f98] mb-3 pl-1">
                      Excluded Entities
                    </label>
                    <textarea
                      value={excluded}
                      onChange={(e) => setExcluded(e.target.value)}
                      className="input-field min-h-[140px] resize-y font-medium text-sm leading-relaxed"
                      placeholder="List companies to strictly avoid..."
                    />
                  </div>

                  <div className="bg-[#0a0a0f] border border-white/5 p-6 rounded-2xl relative overflow-hidden group shadow-inner">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                      <Sparkles size={60} className="text-[#8b5cf6] -mr-4 -mt-4 text-glow" />
                    </div>
                    
                    <label className="block text-[10px] font-bold uppercase tracking-widest text-[#06b6d4] mb-4">
                      Compensation Floor
                    </label>
                    <div className="flex items-center gap-4 border-b border-white/10 pb-2 focus-within:border-[#06b6d4]/50 transition-colors relative z-10">
                      <span className="text-3xl font-light text-white">$</span>
                      <input
                        type="number"
                        value={minSalary}
                        onChange={(e) => setMinSalary(Number(e.target.value))}
                        className="bg-transparent border-none outline-none text-4xl font-light w-full text-white"
                        min={0}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold uppercase tracking-widest text-[#a39f98] mb-3 pl-1">
                      Primary Country
                    </label>
                    <input
                      type="text"
                      value={country}
                      onChange={(e) => setCountry(e.target.value)}
                      className="input-field max-w-full"
                      placeholder="e.g. United States, United Kingdom, Worldwide"
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold uppercase tracking-widest text-[#a39f98] mb-3 pl-1">
                      Workplace Type
                    </label>
                    <select
                      value={workplaceType}
                      onChange={(e) => setWorkplaceType(e.target.value)}
                      className="bg-[#0a0a0f] border border-white/5 rounded-2xl px-5 py-4 w-full text-white appearance-none outline-none focus:border-[#06b6d4]/40 cursor-pointer"
                    >
                      <option value="Any">Any Mode (Remote / On-site / Hybrid)</option>
                      <option value="Remote">Strictly Remote</option>
                      <option value="Hybrid">Hybrid Roles</option>
                      <option value="On-site">On-site Office</option>
                    </select>
                  </div>
                </div>

              </div>

              {/* Footer Actions */}
              <div className="mt-12 pt-8 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-6">
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
                  {saving ? "Synchronizing..." : "Save Preferences"}
                </button>
              </div>

            </GlassCard>
          </form>
        </motion.div>
      )}
    </PageContainer>
  );
}
