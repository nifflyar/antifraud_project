"use client";

import React, { useEffect, useState, useCallback } from "react";
import { dashboard, reports } from "@/lib/api";
import { astanaDateInput, astanaDateInputDaysAgo, formatAstanaShortDate } from "@/lib/datetime";
import type { DashboardSummary, RiskTrendItem, RiskConcentrationItem } from "@/types/api";
import KPICard from "@/components/KPICard";
import LoadingState from "@/components/LoadingState";
import {
  RefreshCw, TrendingUp, BarChart3, Building2, Armchair, Users, AlertTriangle,
  ShieldAlert, Percent, Radio, MapPin, Calendar, Download, PieChart
} from "lucide-react";
import { motion } from "framer-motion";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart as RechartsPie, Pie, Cell, Legend,
} from "recharts";

const RISK_COLORS: Record<string, string> = {
  critical: "#f43f5e",
  high: "#f97316",
  medium: "#fbbf24",
  low: "#34d399",
};

function DownloadButton({
  label,
  period,
}: {
  label: string;
  period: "week" | "month";
}) {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      const now = new Date();
      const dateTo = astanaDateInput(now);
      const dateFrom = astanaDateInputDaysAgo(period === "week" ? 6 : 29);

      const res = await reports.suspiciousExcel({ date_from: dateFrom, date_to: dateTo });
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `risk_report_${period}_${dateTo}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Download error:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      className="btn btn-secondary btn-sm"
      onClick={handleDownload}
      disabled={loading}
      style={{ gap: 6 }}
    >
      <Download size={14} />
      {loading ? "Загрузка..." : label}
    </button>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trend, setTrend] = useState<RiskTrendItem[]>([]);
  const [channels, setChannels] = useState<RiskConcentrationItem[]>([]);
  const [terminals, setTerminals] = useState<RiskConcentrationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [trendLoading, setTrendLoading] = useState(false);

  // Date filters for trend
  const [trendDateFrom, setTrendDateFrom] = useState("");
  const [trendDateTo, setTrendDateTo] = useState("");

  const applyTrendPeriod = (period: "week" | "month" | "quarter" | "year" | "all") => {
    if (period === "all") {
      setTrendDateFrom("");
      setTrendDateTo("");
      return;
    }
    const now = new Date();
    let daysBack = 30;
    if (period === "week") daysBack = 7;
    else if (period === "month") daysBack = 30;
    else if (period === "quarter") daysBack = 90;
    else if (period === "year") daysBack = 365;

    const from = new Date(now.getTime() - daysBack * 24 * 60 * 60 * 1000);
    setTrendDateFrom(astanaDateInput(from));
    setTrendDateTo(astanaDateInput(now));
  };

  const fetchSummaryAndConcentration = useCallback(async () => {
    setLoading(true);
    try {
      const [s, ch, te] = await Promise.all([
        dashboard.summary(),
        dashboard.riskConcentration("CHANNEL"),
        dashboard.riskConcentration("TERMINAL"),
      ]);
      setSummary(s);
      setChannels(ch.items || []);
      setTerminals(te.items || []);
    } catch (e) {
      console.error("Dashboard fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchTrend = useCallback(async () => {
    setTrendLoading(true);
    try {
      const t = await dashboard.riskTrend(trendDateFrom || undefined, trendDateTo || undefined);
      setTrend(t.items || []);
    } catch (e) {
      console.error("Trend fetch error:", e);
    } finally {
      setTrendLoading(false);
    }
  }, [trendDateFrom, trendDateTo]);

  const fetchAll = useCallback(() => {
    fetchSummaryAndConcentration();
    fetchTrend();
  }, [fetchSummaryAndConcentration, fetchTrend]);

  useEffect(() => {
    fetchSummaryAndConcentration();
  }, [fetchSummaryAndConcentration]);

  useEffect(() => {
    fetchTrend();
  }, [fetchTrend]);

  const trendData = trend.map((item) => ({
    date: formatAstanaShortDate(item.date),
    highrisk: item.highrisk_ops,
    share: item.share,
    total: item.total_ops,
  }));

  const channelData = channels.slice(0, 6).map((item) => ({
    name: item.dimension_value,
    value: +(item.share_highrisk_ops * 100).toFixed(1),
  }));

  const terminalData = terminals.slice(0, 6).map((item) => ({
    name: item.dimension_value,
    lift: +((item.lift_vs_base - 1) * 100).toFixed(0),
  }));

  const seatData = trend.map((item, idx) => ({
    week: `W${idx + 1}`,
    cases: Math.floor(item.highrisk_ops * 0.4),
  }));

  // Risk distribution pie data
  const riskPieData = summary
    ? [
      { name: "Critical", value: summary.critical_risk_count, color: RISK_COLORS.critical, pct: summary.critical_risk_pct },
      { name: "High", value: summary.high_risk_count, color: RISK_COLORS.high, pct: summary.high_risk_pct },
      { name: "Medium", value: summary.medium_risk_count, color: RISK_COLORS.medium, pct: summary.medium_risk_pct },
      { name: "Low", value: summary.low_risk_count, color: RISK_COLORS.low, pct: summary.low_risk_pct },
    ].filter((d) => d.value > 0)
    : [];

  const tooltipStyle = {
    borderRadius: 14,
    border: "1px solid rgba(255,255,255,0.08)",
    boxShadow: "0 10px 30px rgba(0,0,0,0.8)",
    fontSize: 13,
    padding: "10px 14px",
    background: "rgba(15,17,26,0.8)",
    backdropFilter: "blur(16px)",
    color: "#f8fafc",
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.08 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, scale: 0.95, y: 15 },
    show: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: { type: "spring" as const, stiffness: 200, damping: 20 },
    },
  };

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Дашборд аналитики</h1>
          <p className="page-subtitle">Глобальный мониторинг рисковых операций</p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <DownloadButton label="Выгрузка за неделю" period="week" />
          <DownloadButton label="Выгрузка за месяц" period="month" />
          <button className="btn btn-primary" onClick={fetchAll} disabled={loading || trendLoading}>
            <RefreshCw size={16} className={loading || trendLoading ? "spinning" : ""} />
            Обновить
          </button>
        </div>
      </div>

      {/* KPI Cards - Loading */}
      {loading && !summary && (
        <LoadingState variant="skeleton-grid" skeletonCount={6} message="Загрузка аналитики" />
      )}

      {/* KPI Cards - Data */}
      {summary && (
        <motion.div variants={containerVariants} initial="hidden" animate="show" className="kpi-grid">
          <motion.div variants={itemVariants} style={{ height: "100%" }}>
            <KPICard label="Всего пассажиров" value={summary.total_passengers.toLocaleString()} icon={<Users size={22} />} />
          </motion.div>
          <motion.div variants={itemVariants} style={{ height: "100%" }}>
            <KPICard
              label="High Risk"
              value={summary.high_risk_count}
              variant="warning"
              icon={<AlertTriangle size={22} />}
              subtitle={`${summary.high_risk_pct?.toFixed(1) ?? "—"}% от общего`}
            />
          </motion.div>
          <motion.div variants={itemVariants} style={{ height: "100%" }}>
            <KPICard
              label="Critical Risk"
              value={summary.critical_risk_count}
              variant="danger"
              icon={<ShieldAlert size={22} />}
              subtitle={`${summary.critical_risk_pct?.toFixed(1) ?? "—"}% — ТРЕБУЮТ ПРОВЕРКИ`}
            />
          </motion.div>
          <motion.div variants={itemVariants} style={{ height: "100%" }}>
            <KPICard
              label="Доля рисков (High+Critical)"
              value={`${((summary.high_risk_pct ?? 0) + (summary.critical_risk_pct ?? 0)).toFixed(1)}%`}
              icon={<Percent size={22} />}
              subtitle={`Medium: ${summary.medium_risk_pct?.toFixed(1) ?? "—"}% / Low: ${summary.low_risk_pct?.toFixed(1) ?? "—"}%`}
            />
          </motion.div>
          <motion.div variants={itemVariants} style={{ height: "100%" }}>
            <KPICard
              label="Подозрительных операций"
              value={`${summary.share_suspicious_ops?.toFixed(1) ?? "0.0"}%`}
              variant="warning"
              icon={<Percent size={22} />}
              subtitle="operation-level, без обычных возвратов"
            />
          </motion.div>
          <motion.div variants={itemVariants} style={{ height: "100%" }}>
            <KPICard label="Топ канал" value={summary.top_risk_channel || "—"} subtitle="высшая концентрация" icon={<Radio size={22} />} />
          </motion.div>
          <motion.div variants={itemVariants} style={{ height: "100%" }}>
            <KPICard label="Топ терминал" value={summary.top_risk_terminal || "—"} subtitle="lift фактор" icon={<MapPin size={22} />} />
          </motion.div>
        </motion.div>
      )}

      {/* Risk Distribution + Trend Row */}
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid-2" style={{ marginBottom: 24 }}>
        {/* Pie chart — risk distribution */}
        <motion.div variants={itemVariants} className="card chart-card">
          <div className="chart-title">
            <div className="chart-icon" style={{ background: "rgba(99,102,241,0.15)", color: "#818cf8", width: 32, height: 32, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", padding: 7 }}>
              <PieChart size={18} />
            </div>
            Распределение по уровням риска
          </div>
          {loading ? (
            <LoadingState variant="inline" message="Загрузка графика" showTimer={false} />
          ) : riskPieData.length === 0 ? (
            <div className="empty-state" style={{ height: 260, display: "flex", flexDirection: "column", justifyContent: "center" }}>
              <p style={{ fontSize: "0.8125rem" }}>Нет данных</p>
            </div>
          ) : (
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <ResponsiveContainer width="55%" height={240}>
                <RechartsPie>
                  <Pie
                    data={riskPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {riskPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value, name) => [`${Number(value ?? 0)} пасс.`, String(name)]}
                  />
                </RechartsPie>
              </ResponsiveContainer>
              <div style={{ flex: 1 }}>
                {riskPieData.map((d) => (
                  <div key={d.name} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <div style={{ width: 10, height: 10, borderRadius: "50%", background: d.color, boxShadow: `0 0 6px ${d.color}` }} />
                      <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", fontWeight: 600 }}>{d.name}</span>
                    </div>
                    <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                      <span className="mono" style={{ fontSize: "0.875rem", fontWeight: 800, color: d.color }}>{d.pct?.toFixed(1) ?? "—"}%</span>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{d.value.toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>

        {/* Trend Chart */}
        <motion.div variants={itemVariants} className="card chart-card">
          <div className="chart-title" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div className="chart-icon" style={{ background: "rgba(249, 115, 22, 0.15)", color: "#f97316", width: 32, height: 32, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", padding: 7 }}>
                <TrendingUp size={18} />
              </div>
              Динамика риска
            </div>
            {/* Date Picker */}
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", justifyContent: "flex-end" }}>
              <button className="btn btn-secondary btn-sm" onClick={() => applyTrendPeriod("week")}>7 дней</button>
              <button className="btn btn-secondary btn-sm" onClick={() => applyTrendPeriod("month")}>30 дней</button>
              <button className="btn btn-secondary btn-sm" onClick={() => applyTrendPeriod("quarter")}>90 дней</button>
              <button className="btn btn-secondary btn-sm" onClick={() => applyTrendPeriod("year")}>Год</button>
              <button className="btn btn-ghost btn-sm" onClick={() => applyTrendPeriod("all")}>Всё</button>
              <div style={{ display: "flex", alignItems: "center", background: "var(--bg-secondary)", borderRadius: "var(--radius-sm)", padding: "4px 8px", border: "1px solid var(--border)" }}>
                <Calendar size={12} style={{ color: "var(--text-muted)", marginRight: 6 }} />
                <input
                  className="input"
                  type="date"
                  value={trendDateFrom}
                  onChange={(e) => setTrendDateFrom(e.target.value)}
                  style={{ width: 132, height: 30, fontSize: "0.75rem", colorScheme: "dark" }}
                  title="Дата начала"
                />
              </div>
              <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>—</span>
              <div style={{ display: "flex", alignItems: "center", background: "var(--bg-secondary)", borderRadius: "var(--radius-sm)", padding: "4px 8px", border: "1px solid var(--border)" }}>
                <Calendar size={12} style={{ color: "var(--text-muted)", marginRight: 6 }} />
                <input
                  className="input"
                  type="date"
                  value={trendDateTo}
                  onChange={(e) => setTrendDateTo(e.target.value)}
                  style={{ width: 132, height: 30, fontSize: "0.75rem", colorScheme: "dark" }}
                  title="Дата окончания"
                />
              </div>
            </div>
          </div>
          {trendLoading && !trend.length ? (
            <LoadingState variant="inline" message="Загрузка графика" showTimer={false} />
          ) : trend.length === 0 ? (
            <div className="empty-state" style={{ height: 240, display: "flex", flexDirection: "column", justifyContent: "center" }}>
              <p style={{ fontSize: "0.8125rem" }}>Нет данных за выбранный период</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="gradOrange" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.6} />
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} dy={10} />
                <YAxis tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} dx={-10} />
                <Tooltip contentStyle={tooltipStyle} itemStyle={{ color: "#f97316" }} />
                <Area type="monotone" dataKey="highrisk" stroke="#f97316" strokeWidth={3} fill="url(#gradOrange)" name="High Risk" />
                <Area type="monotone" dataKey="share" stroke="#f43f5e" strokeWidth={2} fillOpacity={0} name="Доля, %" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </motion.div>
      </motion.div>

      {/* Charts Row 2 */}
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid-2" style={{ marginBottom: 24 }}>
        <motion.div variants={itemVariants} className="card chart-card">
          <div className="chart-title">
            <div className="chart-icon" style={{ background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8", width: 32, height: 32, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", padding: 7 }}>
              <BarChart3 size={18} />
            </div>
            Риск по каналам продаж (%)
          </div>
          {loading ? (
            <LoadingState variant="inline" message="Загрузка графика" showTimer={false} />
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={channelData}>
                <defs>
                  <linearGradient id="gradBlue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#38bdf8" />
                    <stop offset="100%" stopColor="#6366f1" />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} dy={10} />
                <YAxis tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} dx={-10} unit="%" />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.03)" }} formatter={(v) => [`${Number(v ?? 0)}%`, "Доля High Risk"]} />
                <Bar dataKey="value" fill="url(#gradBlue)" radius={[6, 6, 0, 0]} maxBarSize={40} name="Доля High Risk" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </motion.div>

        <motion.div variants={itemVariants} className="card chart-card" transition={{ delay: 0.1 }}>
          <div className="chart-title">
            <div className="chart-icon" style={{ background: "rgba(244, 63, 94, 0.15)", color: "#f43f5e", width: 32, height: 32, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", padding: 7 }}>
              <Building2 size={18} />
            </div>
            Risk Lift по терминалам (топ-6)
          </div>
          {loading ? (
            <LoadingState variant="inline" message="Загрузка графика" showTimer={false} />
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={terminalData}>
                <defs>
                  <linearGradient id="gradRed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f43f5e" />
                    <stop offset="100%" stopColor="#9333ea" />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} dy={10} />
                <YAxis tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} dx={-10} unit="%" />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.03)" }} formatter={(v) => {
                  const value = Number(v ?? 0);
                  return [`${value > 0 ? "+" : ""}${value}%`, "Lift vs base"];
                }} />
                <Bar dataKey="lift" fill="url(#gradRed)" radius={[6, 6, 0, 0]} maxBarSize={40} name="Lift vs base" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </motion.div>
      </motion.div>

      {/* Seat blocking chart */}
      <motion.div variants={containerVariants} initial="hidden" animate="show">
        <motion.div variants={itemVariants} className="card chart-card" transition={{ delay: 0.15 }}>
          <div className="chart-title">
            <div className="chart-icon" style={{ background: "rgba(147, 51, 234, 0.15)", color: "#c084fc", width: 32, height: 32, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", padding: 7 }}>
              <Armchair size={18} />
            </div>
            Seat-blocking кейсы (тренд)
          </div>
          {trendLoading && !trend.length ? (
            <LoadingState variant="inline" message="Загрузка графика" showTimer={false} />
          ) : trend.length === 0 ? (
            <div className="empty-state" style={{ height: 200, display: "flex", flexDirection: "column", justifyContent: "center" }}>
              <p style={{ fontSize: "0.8125rem" }}>Нет данных за выбранный период</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={seatData}>
                <defs>
                  <linearGradient id="gradIndigo" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#c084fc" stopOpacity={0.6} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="week" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} dy={10} />
                <YAxis tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} dx={-10} />
                <Tooltip contentStyle={tooltipStyle} itemStyle={{ color: "#c084fc" }} />
                <Area type="monotone" dataKey="cases" stroke="#c084fc" strokeWidth={3} fill="url(#gradIndigo)" name="Кейсов" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </motion.div>
      </motion.div>
    </div>
  );
}
