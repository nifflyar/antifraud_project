"use client";

import React, { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Shield, Mail, Lock, User, ArrowRight, AlertCircle } from "lucide-react";
import { motion } from "framer-motion";

export default function RegisterPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name: fullName, is_admin: false }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: "Ошибка регистрации" }));
        setError(body.detail || "Ошибка регистрации");
        setLoading(false);
        return;
      }
      const ok = await login(email, password);
      setLoading(false);
      if (ok) router.push("/");
      else setError("Ошибка авторизации после регистрации");
    } catch {
      setError("Ошибка сервера");
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <motion.div
        className="card auth-card"
        initial={{ opacity: 0, y: 24, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="auth-logo">
          <div className="auth-logo-icon"><Shield size={26} /></div>
          <div>
            <div className="auth-logo-text">RiskGuard</div>
            <div style={{ fontSize: "0.6875rem", fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase", marginTop: 2 }}>Security Analytics</div>
          </div>
        </div>

        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 800, letterSpacing: "-0.02em" }}>Регистрация</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginTop: 8, lineHeight: 1.5 }}>
            Создайте аккаунт для доступа к платформе
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Полное имя</label>
            <div className="input-icon-wrapper">
              <User size={18} className="input-icon" />
              <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Иванов Иван Иванович" required autoFocus />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <div className="input-icon-wrapper">
              <Mail size={18} className="input-icon" />
              <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email@example.com" required />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Пароль</label>
            <div className="input-icon-wrapper">
              <Lock size={18} className="input-icon" />
              <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
            </div>
          </div>

          {error && (
            <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
              style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 16px", borderRadius: "var(--radius-sm)", background: "var(--risk-critical-bg)", color: "var(--risk-critical)", fontSize: "0.8125rem", fontWeight: 600, marginBottom: 20, border: "1px solid rgba(225, 29, 72, 0.12)" }}>
              <AlertCircle size={16} /> {error}
            </motion.div>
          )}

          <button type="submit" className="btn btn-primary" disabled={loading}
            style={{ width: "100%", padding: "13px 20px", fontSize: "0.9375rem", marginTop: 4 }}>
            {loading ? "Регистрация..." : <>Создать аккаунт <ArrowRight size={18} /></>}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: 28, fontSize: "0.8125rem", color: "var(--text-muted)" }}>
          Уже есть аккаунт?{" "}
          <Link href="/login" style={{ color: "var(--accent)", fontWeight: 600, textDecoration: "none" }}>Войти</Link>
        </div>
      </motion.div>
    </div>
  );
}
