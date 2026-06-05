import React from "react";

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  color?: string;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "neutral";
}

export default function MetricCard({ label, value, unit, color = "inherit", icon, trend }: MetricCardProps) {
  const trendColor = trend === "up" ? "var(--risk-critical)" : trend === "down" ? "var(--risk-low)" : "inherit";

  return (
    <div style={{
      padding: 16,
      borderRadius: "var(--radius-md)",
      background: "var(--bg-secondary)",
      border: "1px solid var(--border)",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
    }}>
      <div style={{ flex: 1 }}>
        <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginBottom: 4 }}>{label}</p>
        <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
          <p className="mono" style={{ fontWeight: 800, fontSize: "1.25rem", color }}>{value}</p>
          {unit && <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{unit}</span>}
        </div>
      </div>
      {icon && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end" }}>
          {icon}
        </div>
      )}
    </div>
  );
}
