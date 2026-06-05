"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  LayoutDashboard,
  Users,
  ArrowLeftRight,
  BarChart3,
  MapPin,
  Upload,
  FileText,
  UserCog,
  ScrollText,
  LogOut,
  Shield,
  Sun,
  Moon,
} from "lucide-react";

const navSections = [
  {
    items: [
      { href: "/", label: "Дашборд", icon: LayoutDashboard },
      { href: "/passengers", label: "Пассажиры", icon: Users },
      { href: "/operations", label: "Операции", icon: ArrowLeftRight },
      { href: "/terminals", label: "Терминалы", icon: MapPin },
      { href: "/concentration", label: "Концентрация", icon: BarChart3 },
    ],
  },
  {
    title: "Инструменты",
    items: [
      { href: "/upload", label: "Загрузка данных", icon: Upload },
      { href: "/reports", label: "Экспорт отчетов", icon: FileText },
    ],
  },
  {
    title: "Администрирование",
    admin: true,
    items: [
      { href: "/users", label: "Пользователи", icon: UserCog },
      { href: "/audit", label: "Аудит логи", icon: ScrollText },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const savedTheme = localStorage.getItem("riskguard_theme");
    if (savedTheme === "light") {
      setTheme("light");
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
  }, []);

  const toggleTheme = () => {
    if (theme === "dark") {
      setTheme("light");
      document.documentElement.setAttribute("data-theme", "light");
      localStorage.setItem("riskguard_theme", "light");
    } else {
      setTheme("dark");
      document.documentElement.removeAttribute("data-theme");
      localStorage.setItem("riskguard_theme", "dark");
    }
  };

  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : "??";

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div
        style={{
          padding: "32px 24px",
          borderBottom: "1px solid rgba(255,255,255,0.05)",
        }}
      >
        <Link
          href="/"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            textDecoration: "none",
          }}
        >
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: "var(--radius-md)",
              background: "var(--accent-gradient)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "white",
              boxShadow: "var(--accent-glow)",
            }}
          >
            <Shield size={22} />
          </div>
          <div>
            <div
              style={{
                fontWeight: 800,
                fontSize: "1.25rem",
                color: "var(--text-primary)",
                letterSpacing: "-0.02em",
              }}
            >
              RiskGuard
            </div>
            <div
              style={{
                fontSize: "0.5625rem",
                fontWeight: 700,
                color: "var(--accent-hover)",
                letterSpacing: "0.15em",
                textTransform: "uppercase",
              }}
            >
              Security Analytics
            </div>
          </div>
        </Link>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: "auto", padding: "24px 12px" }}>
        {navSections.map((section, idx) => {
          if (section.admin && !user?.is_admin) return null;
          return (
            <div key={idx} style={{ marginBottom: "16px" }}>
              {section.title && (
                <div className="sidebar-section">{section.title}</div>
              )}
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`sidebar-item ${isActive ? "active" : ""}`}
                  >
                    <Icon size={18} strokeWidth={isActive ? 2.2 : 1.8} />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>

      {/* Profile Footer */}
      <div
        style={{
          padding: "24px 16px",
          borderTop: "1px solid rgba(255,255,255,0.05)",
          background: "rgba(0,0,0,0)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            padding: "16px",
            borderRadius: "var(--radius-md)",
            background: "rgba(255,255,255,0.03)",
            backdropFilter: "blur(10px)",
            marginBottom: 12,
            border: "1px solid rgba(255,255,255,0.05)",
          }}
        >
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: "var(--radius-sm)",
              background: "var(--accent-gradient)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "white",
              fontSize: "0.875rem",
              fontWeight: 800,
              boxShadow: "var(--accent-glow)",
              letterSpacing: "0.02em",
            }}
          >
            {initials}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div
              style={{
                fontSize: "0.9375rem",
                fontWeight: 700,
                color: "var(--text-primary)",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {user?.full_name || "..."}
            </div>
            <div
              style={{
                fontSize: "0.75rem",
                color: "var(--accent-hover)",
                fontWeight: 600,
              }}
            >
              {user?.is_admin ? "Администратор" : "Аналитик"}
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <button
            onClick={toggleTheme}
            className="btn btn-ghost"
            style={{
              flex: 1,
              padding: "8px",
              justifyContent: "center",
              border: "1px solid rgba(255,255,255,0.05)",
              borderRadius: "var(--radius-sm)",
              color: "var(--text-muted)",
            }}
            title={
              theme === "dark"
                ? "Включить светлую тему"
                : "Включить темную тему"
            }
          >
            {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          <button
            onClick={logout}
            className="btn btn-ghost"
            style={{
              flex: 3,
              justifyContent: "center",
              color: "var(--text-muted)",
              fontSize: "0.8125rem",
              border: "1px solid rgba(255,255,255,0.05)",
              borderRadius: "var(--radius-sm)",
            }}
          >
            <LogOut size={16} /> Выйти
          </button>
        </div>
      </div>
    </aside>
  );
}
