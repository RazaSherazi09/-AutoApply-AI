"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { motion, AnimatePresence } from "framer-motion";
import { User, LogOut, LayoutDashboard } from "lucide-react";
import { cn } from "@/lib/utils";

export default function TopNav() {
  const [scrolled, setScrolled] = useState(false);
  const { isAuthenticated, userEmail, logout } = useAuth();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const links = [
    { href: "/jobs", label: "Jobs" },
    { href: "/matches", label: "Matches" },
    { href: "/applications", label: "Applications" },
    { href: "/resumes", label: "Resumes" },
    { href: "/preferences", label: "Preferences" },
  ];

  return (
    <header
      className={cn(
        "fixed top-0 w-full z-50 transition-all duration-500",
        scrolled ? "bg-[#0b0b0f]/90 backdrop-blur-xl border-b border-white/5 py-4" : "bg-transparent py-6"
      )}
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8 flex items-center justify-between">
        
        {/* Left: Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-[#d6b98c] to-[#c8a97e] flex items-center justify-center text-[#111] font-bold text-lg font-serif group-hover:scale-105 transition-transform">
            A
          </div>
          <span className="font-serif text-xl tracking-wide text-white">AutoApply AI</span>
        </Link>

        {/* Center: Nav */}
        <nav className="hidden md:flex items-center gap-8">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-[#a39f98] hover:text-[#d6b98c] transition-colors tracking-wide"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Right: Auth / Dashboard */}
        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <div className="flex items-center gap-4">
              <Link
                href="/dashboard"
                className="hidden sm:flex items-center gap-2 text-sm text-[#a39f98] hover:text-white transition-colors"
              >
                <LayoutDashboard size={16} /> Dashboard
              </Link>
              <div className="h-4 w-px bg-white/10 hidden sm:block" />
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-[#d6b98c]">
                  <User size={16} />
                </div>
                <button
                  onClick={logout}
                  className="text-[#a39f98] hover:text-red-400 transition-colors"
                  title="Sign out"
                >
                  <LogOut size={16} />
                </button>
              </div>
            </div>
          ) : (
            <Link href="/login" className="btn-primary py-2 px-6">
              Sign In
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
