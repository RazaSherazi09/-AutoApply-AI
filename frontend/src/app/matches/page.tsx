"use client";

import { useEffect, useState } from "react";
import { matchesApi } from "@/lib/api";
import { motion } from "framer-motion";
import PageContainer from "@/components/PageContainer";
import MatchCard from "@/components/MatchCard";

export default function MatchesPage() {
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("PENDING_APPROVAL");

  async function loadMatches() {
    setLoading(true);
    try {
      let params = "?limit=50";
      if (statusFilter !== "All") params += `&status_filter=${statusFilter}`;
      const data = await matchesApi.list(params);
      setMatches(data.items);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadMatches(); }, [statusFilter]);

  const handleApprove = async (id: string) => {
    try {
      await matchesApi.approve(Number(id));
      await loadMatches();
    } catch { }
  };

  const handleReject = async (id: string) => {
    try {
      await matchesApi.reject(Number(id));
      await loadMatches();
    } catch { }
  };

  return (
    <PageContainer>
      <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <motion.h1 
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} 
            className="page-title mb-2"
          >
            Matches
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
            className="text-[var(--muted-fg)] text-lg"
          >
            Review opportunities selected by the matching engine.
          </motion.p>
        </div>
        
        <motion.div 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          className="flex items-center gap-4 border border-[var(--border)] px-5 py-3"
        >
          <span className="label-upper">Filter</span>
          <div className="h-4 w-px bg-[var(--border)]" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-transparent text-[var(--foreground)] outline-none cursor-pointer appearance-none min-w-[140px] font-medium text-sm"
          >
            <option value="PENDING_APPROVAL">Pending</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
            <option value="All">All</option>
          </select>
        </motion.div>
      </header>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[var(--accent)]" />
        </div>
      ) : matches.length === 0 ? (
        <div className="text-center py-20 border border-[var(--border)]">
          <p className="text-2xl font-bold text-[var(--foreground)] tracking-tight mb-2" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>Queue empty.</p>
          <p className="text-sm text-[var(--muted-fg)] font-mono uppercase tracking-wider">No matches require attention</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {matches.map((m, i) => (
            <motion.div
              key={m.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05, duration: 0.4, ease: [0.25, 0, 0, 1] }}
            >
              <MatchCard 
                match={m}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            </motion.div>
          ))}
        </div>
      )}
    </PageContainer>
  );
}
