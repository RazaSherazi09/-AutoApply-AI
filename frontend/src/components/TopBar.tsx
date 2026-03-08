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
      <header className="fixed top-0 left-0 right-0 h-[72px] bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/5 z-50 transition-all duration-300">
        <div className="max-w-[1240px] mx-auto w-full h-full px-6 flex items-center justify-between">
          
          {/* Logo */}
          <Link href="/dashboard" className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#06b6d4] to-[#8b5cf6] flex items-center justify-center text-white font-bold text-lg font-sans">
              A
            </div>
            <span className="font-sans text-lg font-semibold tracking-wide text-white">AutoApply AI</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1 xl:gap-2">
            {centerLinks.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "relative px-4 py-2 text-sm font-medium transition-colors duration-200 rounded-md hover:bg-white/5 hover:text-white",
                    active ? "text-white" : "text-[#a39f98]"
                  )}
                >
                  {link.label}
                  {active && (
                    <span className="absolute left-0 right-0 bottom-0 h-[2px] bg-gradient-to-r from-[#06b6d4] to-[#8b5cf6] rounded-t-sm" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Desktop Right Actions */}
          <div className="hidden md:flex items-center gap-3">
            <Link href="/preferences" className="w-10 h-10 rounded-full flex items-center justify-center text-[#a39f98] hover:text-white hover:bg-white/5 transition-colors">
              <Sliders size={18} />
            </Link>
            <Link href="/settings" className="w-10 h-10 rounded-full flex items-center justify-center text-[#a39f98] hover:text-white hover:bg-white/5 transition-colors">
              <Settings size={18} />
            </Link>
            
            <div className="h-6 w-px bg-white/10 mx-1" />

            <div className="flex items-center gap-3 pl-2 relative group cursor-pointer">
              <div className="flex flex-col items-end">
                <span className="text-sm font-medium text-white max-w-[120px] truncate">{userEmail}</span>
                <span className="text-[10px] text-[#06b6d4] uppercase tracking-widest font-semibold">Premium</span>
              </div>
              <div className="w-10 h-10 rounded-full bg-[#0f0f23] border border-white/10 flex items-center justify-center text-[#8b5cf6]">
                <User size={18} />
              </div>
              
              {/* Dropdown Menu (on hover) */}
              <div className="absolute top-full right-0 pt-4 opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-all duration-200">
                <div className="w-48 bg-[#0f0f23] border border-white/5 rounded-xl shadow-xl overflow-hidden backdrop-blur-xl">
                  <div className="p-2">
                    <button
                      onClick={logout}
                      className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg text-red-400 hover:bg-red-500/10 transition-colors"
                    >
                      <LogOut size={16} />
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Mobile Menu Toggle */}
          <button 
            className="md:hidden w-10 h-10 flex items-center justify-center text-[#a39f98] hover:text-white"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </header>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-40 bg-[#0a0a0f] pt-[72px] flex flex-col md:hidden">
          <nav className="flex-1 overflow-y-auto px-6 py-8 flex flex-col gap-4">
            <p className="text-xs uppercase tracking-widest text-[#a39f98] mb-2 font-semibold">Main Menu</p>
            {centerLinks.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center text-lg font-medium p-3 rounded-lg transition-colors border",
                    active 
                      ? "bg-white/5 text-white border-white/5" 
                      : "text-[#a39f98] border-transparent hover:bg-white/5 hover:text-white"
                  )}
                >
                  {link.label}
                  {active && <span className="ml-auto w-2 h-2 rounded-full bg-[#06b6d4]" />}
                </Link>
              );
            })}
            
            <div className="h-px w-full bg-white/5 my-4" />
            <p className="text-xs uppercase tracking-widest text-[#a39f98] mb-2 font-semibold">Account</p>

            <Link href="/preferences" onClick={() => setMobileMenuOpen(false)} className="flex items-center gap-3 text-base font-medium p-3 rounded-lg text-[#a39f98] hover:bg-white/5 hover:text-white transition-colors">
              <Sliders size={20} /> Preferences
            </Link>
            <Link href="/settings" onClick={() => setMobileMenuOpen(false)} className="flex items-center gap-3 text-base font-medium p-3 rounded-lg text-[#a39f98] hover:bg-white/5 hover:text-white transition-colors">
              <Settings size={20} /> Settings
            </Link>
            <button
              onClick={() => { logout(); setMobileMenuOpen(false); }}
              className="flex items-center gap-3 text-base font-medium p-3 rounded-lg text-red-400 hover:bg-red-500/10 transition-colors mt-auto mb-8"
            >
              <LogOut size={20} /> Sign Out ( {userEmail} )
            </button>
          </nav>
        </div>
      )}
    </>
  );
}
