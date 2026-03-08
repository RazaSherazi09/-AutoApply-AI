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
    <div className="relative min-h-screen selection:bg-[#c8a97e] selection:text-black">
      <TopNav />
      
      {/* Cinematic Background */}
      <div className="absolute inset-0 z-0 overflow-hidden">
        <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-[#d6b98c]/5 rounded-full blur-[120px] mix-blend-screen -translate-y-1/2 translate-x-1/3" />
        <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-[#c8a97e]/5 rounded-full blur-[100px] mix-blend-screen translate-y-1/3 -translate-x-1/3" />
        {/* Subtle noise texture */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")' }}></div>
      </div>

      <main className="relative z-10 pt-40 pb-20 px-6 lg:px-8 max-w-7xl mx-auto flex flex-col items-center justify-center min-h-screen text-center">
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="max-w-4xl mx-auto"
        >
          <span className="inline-block py-1 px-3 rounded-full border border-[#d6b98c]/30 bg-[#c8a97e]/10 text-[#d6b98c] text-xs font-medium tracking-widest uppercase mb-8">
            AI-Powered Job Automation
          </span>
          
          <h1 className="font-serif text-5xl md:text-7xl lg:text-[80px] leading-[1.1] tracking-tight mb-8">
            Your personal agent that <br className="hidden md:block" />
            <span className="gradient-text-gold inline-block mt-2">applies for you.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-[#a39f98] max-w-2xl mx-auto mb-12 font-light leading-relaxed">
            Upload your resume, set your refined preferences, and let our proprietary AI models find, match, and secure the best opportunities seamlessly.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20 md:mb-32">
            <Link href="/login" className="btn-primary text-base py-3.5 px-8 w-full sm:w-auto">
              Start Applying <ArrowRight size={18} />
            </Link>
            <Link href="/resumes" className="btn-secondary text-base py-3.5 px-8 w-full sm:w-auto">
              Upload Resume
            </Link>
          </div>
        </motion.div>

        {/* Large Premium Search Bar component */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-4xl mx-auto"
        >
          <form 
            onSubmit={handleSearch}
            className="glass-card p-3 rounded-2xl md:rounded-full flex flex-col md:flex-row items-center gap-3"
          >
            <div className="flex-1 flex items-center gap-3 px-4 py-2 w-full md:w-auto border-b md:border-b-0 md:border-r border-white/10">
              <Search size={20} className="text-[#c8a97e]" />
              <input 
                type="text" 
                placeholder="Job title, keyword, or company..."
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                className="bg-transparent border-none outline-none text-white w-full placeholder:text-white/40 font-medium"
              />
            </div>
            <div className="flex-1 flex items-center gap-3 px-4 py-2 w-full md:w-auto">
              <MapPin size={20} className="text-[#c8a97e]" />
              <input 
                type="text" 
                placeholder="City, state, or Remote"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="bg-transparent border-none outline-none text-white w-full placeholder:text-white/40 font-medium"
              />
            </div>
            <button 
              type="submit"
              className="w-full md:w-auto bg-white/10 hover:bg-white/20 text-white font-medium py-3 px-8 rounded-xl md:rounded-full transition-colors flex items-center justify-center gap-2 border border-white/5"
            >
              Find Jobs
            </button>
          </form>
        </motion.div>

      </main>
    </div>
  );
}
