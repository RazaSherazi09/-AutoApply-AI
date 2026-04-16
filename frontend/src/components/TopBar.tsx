"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { 
  Settings, Sliders, User, LogOut, Menu, X 
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function TopBar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();
  const { userEmail, logout } = useAuth();

  // Hide TopBar on auth pages
  if (pathname === "/login" || pathname === "/register") {
    return null;
  }

  const centerLinks = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/jobs", label: "Jobs" },
    { href: "/matches", label: "Matches" },
    { href: "/applications", label: "Applications" },
    { href: "/resumes", label: "Resumes" },
  ];

  return (
    <>
      <header className="fixed top-0 left-0 right-0 h-[72px] bg-[var(--background)]/95 backdrop-blur-sm border-b border-[var(--border)] z-50">
        <div className="max-w-5xl mx-auto w-full h-full px-6 md:px-12 lg:px-16 flex items-center justify-between">
          
          {/* Logo */}
          <Link href="/dashboard" className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[var(--accent)] flex items-center justify-center text-[var(--accent-fg)] font-bold text-lg" style={{ fontFamily: 'var(--font-display)' }}>
              A
            </div>
            <span className="text-lg font-semibold tracking-tight text-[var(--foreground)]" style={{ fontFamily: 'var(--font-display)' }}>AutoApply</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-0">
            {centerLinks.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "relative px-4 py-2 text-sm font-medium transition-colors duration-150 tracking-wide uppercase",
                    active ? "text-[var(--foreground)]" : "text-[var(--muted-fg)] hover:text-[var(--foreground)]"
                  )}
                  style={{ letterSpacing: '0.05em' }}
                >
                  {link.label}
                  {active && (
                    <span className="absolute left-4 right-4 bottom-0 h-[2px] bg-[var(--accent)]" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Desktop Right Actions */}
          <div className="hidden md:flex items-center gap-2">
            <Link href="/preferences" className="w-10 h-10 flex items-center justify-center text-[var(--muted-fg)] hover:text-[var(--foreground)] transition-colors">
              <Sliders size={18} strokeWidth={1.5} />
            </Link>
            <Link href="/settings" className="w-10 h-10 flex items-center justify-center text-[var(--muted-fg)] hover:text-[var(--foreground)] transition-colors">
              <Settings size={18} strokeWidth={1.5} />
            </Link>
            
            <div className="h-6 w-px bg-[var(--border)] mx-2" />

            <div className="flex items-center gap-3 pl-2 relative group cursor-pointer">
              <div className="flex flex-col items-end">
                <span className="text-sm font-medium text-[var(--foreground)] max-w-[120px] truncate">{userEmail}</span>
                <span className="text-[10px] text-[var(--accent)] uppercase font-mono tracking-[0.2em]">Active</span>
              </div>
              <div className="w-9 h-9 border border-[var(--border)] flex items-center justify-center text-[var(--muted-fg)]">
                <User size={16} strokeWidth={1.5} />
              </div>
              
              {/* Dropdown Menu */}
              <div className="absolute top-full right-0 pt-4 opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-all duration-150">
                <div className="w-48 bg-[var(--card)] border border-[var(--border)] overflow-hidden">
                  <div className="p-2">
                    <button
                      onClick={logout}
                      className="w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-[var(--error)] hover:bg-[var(--error)]/10 transition-colors uppercase tracking-wider"
                    >
                      <LogOut size={14} strokeWidth={1.5} />
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Mobile Menu Toggle */}
          <button 
            className="md:hidden w-10 h-10 flex items-center justify-center text-[var(--muted-fg)] hover:text-[var(--foreground)]"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} strokeWidth={1.5} /> : <Menu size={24} strokeWidth={1.5} />}
          </button>
        </div>
      </header>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-40 bg-[var(--background)] pt-[72px] flex flex-col md:hidden">
          <nav className="flex-1 overflow-y-auto px-6 py-8 flex flex-col gap-2">
            <p className="label-upper mb-4">Navigation</p>
            {centerLinks.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center justify-between text-lg font-medium p-4 transition-colors border-b border-[var(--border)]",
                    active 
                      ? "text-[var(--foreground)]" 
                      : "text-[var(--muted-fg)] hover:text-[var(--foreground)]"
                  )}
                >
                  <span className="uppercase tracking-wider">{link.label}</span>
                  {active && <span className="w-2 h-[2px] bg-[var(--accent)]" />}
                </Link>
              );
            })}
            
            <div className="h-px w-full bg-[var(--border)] my-6" />
            <p className="label-upper mb-4">Account</p>

            <Link href="/preferences" onClick={() => setMobileMenuOpen(false)} className="flex items-center gap-3 text-base font-medium p-4 text-[var(--muted-fg)] hover:text-[var(--foreground)] transition-colors border-b border-[var(--border)] uppercase tracking-wider">
              <Sliders size={18} strokeWidth={1.5} /> Preferences
            </Link>
            <Link href="/settings" onClick={() => setMobileMenuOpen(false)} className="flex items-center gap-3 text-base font-medium p-4 text-[var(--muted-fg)] hover:text-[var(--foreground)] transition-colors border-b border-[var(--border)] uppercase tracking-wider">
              <Settings size={18} strokeWidth={1.5} /> Settings
            </Link>
            <button
              onClick={() => { logout(); setMobileMenuOpen(false); }}
              className="flex items-center gap-3 text-base font-medium p-4 text-[var(--error)] hover:bg-[var(--error)]/10 transition-colors mt-auto mb-8 uppercase tracking-wider"
            >
              <LogOut size={18} strokeWidth={1.5} /> Sign Out
            </button>
          </nav>
        </div>
      )}
    </>
  );
}
