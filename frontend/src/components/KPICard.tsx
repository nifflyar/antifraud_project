"use client";

import React from "react";

interface KPICardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  variant?: "default" | "warning" | "danger";
  icon?: React.ReactNode;
}

export default function KPICard({ label, value, subtitle, variant = "default", icon }: KPICardProps) {
  const variantClass = variant === "danger" ? "danger" : variant === "warning" ? "warning" : "";

  const iconBg =
    variant === "danger"
      ? "rgba(244, 63, 94, 0.12)"
      : variant === "warning"
      ? "rgba(251, 191, 36, 0.12)"
      : "rgba(99, 102, 241, 0.12)";

  const iconColor =
    variant === "danger"
      ? "var(--risk-critical)"
      : variant === "warning"
      ? "var(--risk-medium)"
      : "var(--accent)";

  return (
    <div className="card kpi-card" style={{ height: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="kpi-label">{label}</div>
          <div className={`kpi-value ${variantClass}`}>{value}</div>
          {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
        </div>
        {icon && (
          <div
            style={{
              width: 48,
              height: 48,
              minWidth: 48,
              borderRadius: "var(--radius-md)",
              background: iconBg,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: iconColor,
              boxShadow: "inset 0 1px 1px rgba(255,255,255,0.1)",
            }}
          >
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
