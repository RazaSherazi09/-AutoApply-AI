"use client";

import { useEffect, useState } from "react";
import { settingsApi } from "@/lib/api";
import { motion } from "framer-motion";
import { Compass } from "lucide-react";
import PageContainer from "@/components/PageContainer";

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
      setMsg("✅ Preferences saved.");
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
          Preferences
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="text-[var(--muted-fg)] text-lg max-w-xl"
        >
          Configure the matching engine. What opportunities do you seek?
        </motion.p>
      </header>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[var(--accent)]" />
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5, ease: [0.25, 0, 0, 1] }}
        >
          <form onSubmit={handleSave}>
            <div className="max-w-4xl border border-[var(--border)] p-8 md:p-12">
              
              <div className="flex items-center gap-3 mb-10 pb-6 border-b border-[var(--border)]">
                <Compass size={20} strokeWidth={1.5} className="text-[var(--accent)]" />
                <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-[var(--foreground)]" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>Career Profile</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                
                {/* Left Column */}
                <div className="space-y-10">
                  <div>
                    <label className="label-upper block mb-3">
                      Desired Titles <span className="text-[var(--accent)]">*</span>
                    </label>
                    <textarea
                      value={titles}
                      onChange={(e) => setTitles(e.target.value)}
                      className="input-field min-h-[140px] resize-y text-sm leading-relaxed"
                      placeholder={"Software Engineer\nHead of Engineering\nDirector of Technology"}
                    />
                    <p className="label-upper mt-2 opacity-60">One per line</p>
                  </div>

                  <div>
                    <label className="label-upper block mb-3">
                      Target Locations
                    </label>
                    <textarea
                      value={locations}
                      onChange={(e) => setLocations(e.target.value)}
                      className="input-field min-h-[140px] resize-y text-sm leading-relaxed"
                      placeholder={"San Francisco, CA\nLondon, UK\nNew York City"}
                    />
                  </div>
                </div>

                {/* Right Column */}
                <div className="space-y-10">
                  <div>
                    <label className="label-upper block mb-3">
                      Excluded Companies
                    </label>
                    <textarea
                      value={excluded}
                      onChange={(e) => setExcluded(e.target.value)}
                      className="input-field min-h-[140px] resize-y text-sm leading-relaxed"
                      placeholder="Companies to avoid..."
                    />
                  </div>

                  {/* Salary */}
                  <div className="border border-[var(--border)] p-6 relative">
                    <div className="absolute top-0 left-0 h-[2px] w-12 bg-[var(--accent)]" />
                    <label className="label-upper block mb-4 text-[var(--accent)]">
                      Minimum Salary
                    </label>
                    <div className="flex items-end gap-3 border-b border-[var(--border)] pb-2 focus-within:border-[var(--accent)] transition-colors">
                      <span className="text-3xl font-light text-[var(--foreground)]" style={{ fontFamily: 'var(--font-display)' }}>$</span>
                      <input
                        type="number"
                        value={minSalary}
                        onChange={(e) => setMinSalary(Number(e.target.value))}
                        className="bg-transparent border-none outline-none text-4xl font-bold w-full text-[var(--foreground)]"
                        style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.06em' }}
                        min={0}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="label-upper block mb-3">
                      Primary Country
                    </label>
                    <input
                      type="text"
                      value={country}
                      onChange={(e) => setCountry(e.target.value)}
                      className="input-field"
                      placeholder="e.g. United States, Worldwide"
                    />
                  </div>

                  <div>
                    <label className="label-upper block mb-3">
                      Workplace Type
                    </label>
                    <select
                      value={workplaceType}
                      onChange={(e) => setWorkplaceType(e.target.value)}
                      className="input-field appearance-none cursor-pointer"
                    >
                      <option value="Any">Any (Remote / On-site / Hybrid)</option>
                      <option value="Remote">Strictly Remote</option>
                      <option value="Hybrid">Hybrid</option>
                      <option value="On-site">On-site</option>
                    </select>
                  </div>
                </div>

              </div>

              {/* Footer */}
              <div className="mt-12 pt-8 border-t border-[var(--border)] flex flex-col sm:flex-row items-center justify-between gap-6">
                <div>
                   {msg && (
                    <motion.span 
                      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                      className={`text-sm font-mono tracking-wide flex items-center gap-2 ${msg.includes("✅") ? "text-[var(--success)]" : "text-[var(--error)]"}`}
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
                  {saving ? "Saving..." : "Save Preferences"}
                </button>
              </div>

            </div>
          </form>
        </motion.div>
      )}
    </PageContainer>
  );
}
