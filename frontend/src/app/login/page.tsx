"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Loader2, Lock, Mail, User, ArrowRight } from "lucide-react";

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
      setSuccess("Account created. Sign in to continue.");
      setIsLogin(true);
      router.push("/login");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[var(--background)]">
      <div className="w-full max-w-md z-10">
        {/* Header */}
        <div className="mb-12">
          <div className="w-12 h-12 bg-[var(--accent)] flex items-center justify-center text-[var(--accent-fg)] font-bold text-2xl mb-8" style={{ fontFamily: 'var(--font-display)' }}>
            A
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-[var(--foreground)] tracking-tighter mb-3" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.06em' }}>
            {isLogin ? "Sign in" : "Create account"}
          </h1>
          <p className="text-[var(--muted-fg)] text-base">
            {isLogin ? "Access your autonomous agent." : "Initialize your job automation system."}
          </p>
        </div>

        {/* Tabs */}
        <div className="flex mb-8 border-b border-[var(--border)]">
          <button
            type="button"
            onClick={() => { setIsLogin(true); setError(""); setSuccess(""); router.push("/login"); }}
            className={`flex-1 py-3 text-sm font-bold uppercase tracking-[0.1em] transition-colors relative ${
              isLogin
                ? "text-[var(--foreground)]"
                : "text-[var(--muted-fg)] hover:text-[var(--foreground)]"
            }`}
          >
            Sign In
            {isLogin && <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-[var(--accent)]" />}
          </button>
          <button
            type="button"
            onClick={() => { setIsLogin(false); setError(""); setSuccess(""); router.push("/register"); }}
            className={`flex-1 py-3 text-sm font-bold uppercase tracking-[0.1em] transition-colors relative ${
              !isLogin
                ? "text-[var(--foreground)]"
                : "text-[var(--muted-fg)] hover:text-[var(--foreground)]"
            }`}
          >
            Create Account
            {!isLogin && <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-[var(--accent)]" />}
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 border border-[var(--error)] text-[var(--error)] text-sm flex items-center gap-3 font-mono">
            <span className="w-1.5 h-1.5 bg-[var(--error)] flex-shrink-0" />
            {error}
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 border border-[var(--success)] text-[var(--success)] text-sm flex items-center gap-3 font-mono">
            <span className="w-1.5 h-1.5 bg-[var(--success)] flex-shrink-0" />
            {success}
          </div>
        )}

        <form onSubmit={isLogin ? handleLogin : handleRegister} className="space-y-6">
          {!isLogin && (
            <div>
              <label className="label-upper block mb-2">
                Full Name
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-[var(--muted-fg)]">
                  <User size={16} strokeWidth={1.5} />
                </div>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="input-field pl-11"
                  placeholder="John Doe"
                  required
                />
              </div>
            </div>
          )}

          <div>
            <label className="label-upper block mb-2">
              Email Address
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-[var(--muted-fg)]">
                <Mail size={16} strokeWidth={1.5} />
              </div>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field pl-11"
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          <div>
            <label className="label-upper block mb-2">
              Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-[var(--muted-fg)]">
                <Lock size={16} strokeWidth={1.5} />
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field pl-11"
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-secondary w-full py-4 text-sm flex items-center justify-center gap-2"
          >
            {loading ? (
              <Loader2 className="animate-spin" size={16} />
            ) : (
              <>
                {isLogin ? "Access Dashboard" : "Initialize Account"}
                <ArrowRight size={16} strokeWidth={1.5} />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
