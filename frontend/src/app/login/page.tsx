"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { authApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import GlassCard from "@/components/GlassCard";
import { Loader2, Lock, Mail, User } from "lucide-react";

export default function AuthPage({ isRegisterDefault = false }: { isRegisterDefault?: boolean }) {
  const [isLogin, setIsLogin] = useState(!isRegisterDefault);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await authApi.login(email, password);
      login(data.access_token, email);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      await authApi.register(email, password, fullName);
      setSuccess("Account created! Please login.");
      setIsLogin(true);
      router.push("/login");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-[#0a0a0f]">
      {/* Premium Background Decoration */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
        <div className="w-[800px] h-[800px] bg-[#06b6d4]/10 rounded-full blur-[120px] absolute -top-40 -left-40" />
        <div className="w-[600px] h-[600px] bg-[#8b5cf6]/10 rounded-full blur-[120px] absolute -bottom-40 -right-20" />
      </div>

      <div className="w-full max-w-md z-10 animate-fade-in">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#06b6d4] to-[#8b5cf6] flex items-center justify-center text-white font-bold text-3xl font-sans mx-auto mb-6 shadow-[0_0_40px_rgba(6,182,212,0.3)]">
            A
          </div>
          <h1 className="text-3xl font-semibold text-white tracking-tight mb-3">
            Welcome to AutoApply AI
          </h1>
          <p className="text-[#a39f98] text-sm">
            Enter your credentials to access your autonomous agent.
          </p>
        </div>

        {/* Card */}
        <GlassCard hoverEffect={false} className="p-8">
          {/* Tabs */}
          <div className="flex mb-8 bg-[#0f0f23] rounded-lg p-1 border border-white/5">
            <button
              type="button"
              onClick={() => { setIsLogin(true); setError(""); setSuccess(""); router.push("/login"); }}
              className={`flex-1 py-2.5 text-sm font-medium rounded-md transition-all duration-300 ${
                isLogin
                  ? "bg-white/10 text-white shadow-sm"
                  : "text-[#a39f98] hover:text-white"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setIsLogin(false); setError(""); setSuccess(""); router.push("/register"); }}
              className={`flex-1 py-2.5 text-sm font-medium rounded-md transition-all duration-300 ${
                !isLogin
                  ? "bg-white/10 text-white shadow-sm"
                  : "text-[#a39f98] hover:text-white"
              }`}
            >
              Create Account
            </button>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-3">
              <div className="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" />
              {error}
            </div>
          )}

          {success && (
            <div className="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-green-400 text-sm flex items-center gap-3">
              <div className="w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0" />
              {success}
            </div>
          )}

          <form onSubmit={isLogin ? handleLogin : handleRegister} className="space-y-5">
            {!isLogin && (
              <div>
                <label className="block text-xs font-medium uppercase tracking-widest text-[#a39f98] mb-2 pl-1">
                  Full Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-[#a39f98]">
                    <User size={18} />
                  </div>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="input-field pl-11 py-3"
                    placeholder="John Doe"
                    required
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium uppercase tracking-widest text-[#a39f98] mb-2 pl-1">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-[#a39f98]">
                  <Mail size={18} />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field pl-11 py-3"
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>

            <div className="pb-2">
              <label className="block text-xs font-medium uppercase tracking-widest text-[#a39f98] mb-2 pl-1">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-[#a39f98]">
                  <Lock size={18} />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pl-11 py-3"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3.5 text-sm font-semibold tracking-wide"
            >
              {loading ? (
                <Loader2 className="animate-spin" size={18} />
              ) : isLogin ? (
                "Access Dashboard"
              ) : (
                "Initialize Account"
              )}
            </button>
          </form>
        </GlassCard>
      </div>
    </div>
  );
}
