"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import TopNav from "@/components/TopNav";
import { Search, MapPin, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Home() {
  const [jobTitle, setJobTitle] = useState("");
  const [location, setLocation] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    router.push(`/jobs?search=${encodeURIComponent(jobTitle)}&location=${encodeURIComponent(location)}`);
  };

  return (
    <div className="relative min-h-screen">
      <TopNav />
      
      <main className="relative z-10 pt-40 pb-20 px-6 md:px-12 lg:px-16 max-w-5xl mx-auto flex flex-col items-start justify-center min-h-screen">
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.25, 0, 0, 1] }}
          className="max-w-4xl w-full"
        >
          {/* Decorative oversized number */}
          <div className="absolute top-32 right-8 text-[12rem] md:text-[20rem] font-black text-[var(--border)]/30 leading-none pointer-events-none select-none hidden lg:block" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.06em' }}>
            AI
          </div>

          <span className="inline-block py-1 px-0 text-[var(--accent)] text-xs font-bold tracking-[0.2em] uppercase mb-8" style={{ fontFamily: 'var(--font-mono)' }}>
            Autonomous Job Agent
          </span>
          
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-[6rem] font-black leading-[1.05] tracking-tighter mb-8" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.06em' }}>
            Your personal<br className="hidden md:block" />
            agent that<br className="hidden md:block" />
            <span className="text-[var(--accent)]">applies for you.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-[var(--muted-fg)] max-w-xl mb-12 leading-relaxed">
            Upload your resume, set your preferences, and let the AI find, match, and secure opportunities — autonomously.
          </p>

          <div className="flex flex-col sm:flex-row items-start gap-6 mb-20 md:mb-32">
            <Link href="/login" className="btn-primary text-base py-3 flex items-center gap-2.5">
              Start Applying <ArrowRight size={18} strokeWidth={1.5} />
            </Link>
            <Link href="/resumes" className="btn-secondary text-base py-3 px-8">
              Upload Resume
            </Link>
          </div>
        </motion.div>

        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2, ease: [0.25, 0, 0, 1] }}
          className="w-full max-w-3xl"
        >
          <form 
            onSubmit={handleSearch}
            className="border border-[var(--border)] p-3 flex flex-col md:flex-row items-center gap-0"
          >
            <div className="flex-1 flex items-center gap-3 px-4 py-3 w-full md:w-auto border-b md:border-b-0 md:border-r border-[var(--border)]">
              <Search size={18} strokeWidth={1.5} className="text-[var(--accent)]" />
              <input 
                type="text" 
                placeholder="Job title, keyword, or company..."
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                className="bg-transparent border-none outline-none text-[var(--foreground)] w-full placeholder:text-[var(--muted-fg)] font-medium"
              />
            </div>
            <div className="flex-1 flex items-center gap-3 px-4 py-3 w-full md:w-auto">
              <MapPin size={18} strokeWidth={1.5} className="text-[var(--accent)]" />
              <input 
                type="text" 
                placeholder="City, state, or Remote"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="bg-transparent border-none outline-none text-[var(--foreground)] w-full placeholder:text-[var(--muted-fg)] font-medium"
              />
            </div>
            <button 
              type="submit"
              className="w-full md:w-auto bg-[var(--foreground)] text-[var(--background)] font-bold py-3 px-8 transition-colors flex items-center justify-center gap-2 uppercase tracking-wider text-sm hover:bg-[var(--accent)] hover:text-[var(--accent-fg)]"
            >
              Find Jobs
            </button>
          </form>
        </motion.div>

      </main>
    </div>
  );
}
