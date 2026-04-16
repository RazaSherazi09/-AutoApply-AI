"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { User, LogOut, LayoutDashboard, ArrowRight } from "lucide-react";
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
  ];

  return (
    <header
      className={cn(
        "fixed top-0 w-full z-50 transition-all duration-300",
        scrolled ? "bg-[var(--background)]/95 backdrop-blur-sm border-b border-[var(--border)] py-4" : "bg-transparent py-6"
      )}
    >
      <div className="max-w-5xl mx-auto px-6 md:px-12 lg:px-16 flex items-center justify-between">
        
        {/* Left: Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 bg-[var(--accent)] flex items-center justify-center text-[var(--accent-fg)] font-bold text-lg" style={{ fontFamily: 'var(--font-display)' }}>
            A
          </div>
          <span className="text-xl font-semibold tracking-tight text-[var(--foreground)]" style={{ fontFamily: 'var(--font-display)' }}>AutoApply</span>
        </Link>

        {/* Center: Nav */}
        <nav className="hidden md:flex items-center gap-8">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="relative text-sm font-medium text-[var(--muted-fg)] hover:text-[var(--foreground)] transition-colors uppercase tracking-[0.05em] group/link"
            >
              {link.label}
              <span className="absolute left-0 right-0 bottom-[-2px] h-px bg-[var(--foreground)] scale-x-0 group-hover/link:scale-x-100 transition-transform origin-left duration-150" />
            </Link>
          ))}
        </nav>

        {/* Right: Auth / Dashboard */}
        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <div className="flex items-center gap-4">
              <Link
                href="/dashboard"
                className="hidden sm:flex items-center gap-2 text-sm text-[var(--muted-fg)] hover:text-[var(--foreground)] transition-colors uppercase tracking-wider"
              >
                <LayoutDashboard size={16} strokeWidth={1.5} /> Dashboard
              </Link>
              <div className="h-4 w-px bg-[var(--border)] hidden sm:block" />
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 border border-[var(--border)] flex items-center justify-center text-[var(--muted-fg)]">
                  <User size={16} strokeWidth={1.5} />
                </div>
                <button
                  onClick={logout}
                  className="text-[var(--muted-fg)] hover:text-[var(--error)] transition-colors"
                  title="Sign out"
                >
                  <LogOut size={16} strokeWidth={1.5} />
                </button>
              </div>
            </div>
          ) : (
            <Link href="/login" className="btn-primary py-2 flex items-center gap-2">
              Sign In <ArrowRight size={16} strokeWidth={1.5} />
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
