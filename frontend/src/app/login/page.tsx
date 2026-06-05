"use client";

import React, { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Shield, Mail, Lock, ArrowRight, AlertCircle } from "lucide-react";
import { motion } from "framer-motion";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const ok = await login(email, password);
    setLoading(false);
    if (ok) {
      router.push("/");
    } else {
      setError("Неверный email или пароль");
    }
  };

  return (
    <div className="auth-page">
      {/* Background Glowing Orbs for Cyberpunk/Enterprise Feel */}
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        style={{
          position: "absolute", top: "20%", left: "30%", width: 400, height: 400,
          background: "var(--accent)", filter: "blur(120px)", borderRadius: "50%", zIndex: 0
        }}
      />
      <motion.div
        animate={{
          scale: [1, 1.5, 1],
          opacity: [0.2, 0.4, 0.2],
        }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        style={{
          position: "absolute", bottom: "10%", right: "20%", width: 500, height: 500,
          background: "var(--risk-critical)", filter: "blur(150px)", borderRadius: "50%", zIndex: 0
        }}
      />

      <motion.div
        className="card auth-card"
        initial={{ opacity: 0, y: 40, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      >
        {/* Logo */}
        <div className="auth-logo">
          <div className="auth-logo-icon">
            <Shield size={28} />
          </div>
          <div>
            <div className="auth-logo-text">RiskGuard</div>
            <div style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--accent-hover)", letterSpacing: "0.15em", textTransform: "uppercase", marginTop: 2 }}>Security Analytics</div>
          </div>
        </div>

        {/* Title */}
        <div style={{ marginBottom: 36 }}>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 800, letterSpacing: "-0.02em" }}>Вход в систему</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem", marginTop: 8, lineHeight: 1.5 }}>
            Подтвердите полномочия для доступа к защищенному модулю
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <div className="input-icon-wrapper">
              <Mail size={18} className="input-icon" />
              <input
                id="email"
                className="input"
                type="email"
                placeholder="admin@riskguard.kz"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Пароль</label>
            <div className="input-icon-wrapper">
              <Lock size={18} className="input-icon" />
              <input
                id="password"
                className="input"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "14px 16px", borderRadius: "var(--radius-md)",
                background: "rgba(244, 63, 94, 0.15)", color: "var(--risk-critical)",
                fontSize: "0.875rem", fontWeight: 600, marginBottom: 24,
                border: "1px solid rgba(244, 63, 94, 0.3)",
                boxShadow: "0 0 15px rgba(244, 63, 94, 0.2)"
              }}
            >
              <AlertCircle size={18} /> {error}
            </motion.div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: "100%", padding: "14px 20px", fontSize: "1rem", marginTop: 8, letterSpacing: "0.02em" }}
          >
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span className="spinning" style={{ display: "inline-flex" }}>⟳</span>
                Аутентификация...
              </span>
            ) : (
              <>Инициировать сессию <ArrowRight size={18} /></>
            )}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: 32, fontSize: "0.875rem", color: "var(--text-muted)" }}>
          Отсутствует допуск?{" "}
          <Link href="/register" style={{ color: "var(--accent-hover)", fontWeight: 600, textDecoration: "none" }}>
            Запрос доступа
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
