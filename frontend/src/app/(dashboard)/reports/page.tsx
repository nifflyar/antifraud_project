"use client";

import React, { useState } from "react";
import { reports } from "@/lib/api";
import { ASTANA_TIMEZONE_LABEL, astanaDateInput, astanaDateInputDaysAgo } from "@/lib/datetime";
import { FileSpreadsheet, FileText, Download, Filter, Calendar, Users } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function ReportsPage() {
  const [passengerIdInput, setPassengerIdInput] = useState("");
  const [downloading, setDownloading] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [passengerRiskBand, setPassengerRiskBand] = useState("");
  const [passengerSearch, setPassengerSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Filters for suspicious excel
  const [trainNo, setTrainNo] = useState("");
  const [cashdesk, setCashdesk] = useState("");
  const [terminal, setTerminal] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const setQuickRange = (days: number | null) => {
    if (days === null) {
      setDateFrom("");
      setDateTo("");
      return;
    }

    setDateFrom(astanaDateInputDaysAgo(days - 1));
    setDateTo(astanaDateInput());
  };

  const downloadFile = async (type: string, fetcher: () => Promise<Response>, filename: string) => {
    setDownloading(type);
    setError(null);
    try {
      const res = await fetcher();
      if (!res.ok) {
        const errorText = await res.text().catch(() => "Download failed");
        throw new Error(errorText || "Download failed");
      }
      const blob = await res.blob();
      if (blob.size === 0) throw new Error("Empty response from server");
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      console.error("Download error:", e);
      setError(`Ошибка при загрузке: ${msg}`);
    } finally {
      setDownloading(null);
    }
  };

  const handleDownloadExcel = () => {
    downloadFile(
      "excel",
      () => reports.suspiciousExcel({
        train_no: trainNo || undefined,
        cashdesk: cashdesk || undefined,
        terminal: terminal || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      }),
      `suspicious_ops_${astanaDateInput()}.xlsx`
    );
  };

  const handleDownloadPassengers = () => {
    const suffix = passengerRiskBand || "all";
    downloadFile(
      "passengers",
      () => reports.passengersExcel({
        risk_band: passengerRiskBand || undefined,
        search: passengerSearch || undefined,
      }),
      `passengers_${suffix}_${astanaDateInput()}.xlsx`
    );
  };

  const reportCards = [
    {
      id: "concentration",
      icon: FileSpreadsheet,
      color: "#3b82f6",
      bg: "#eff6ff",
      title: "Концентрация рисков",
      description: "Сводный отчёт по концентрации рисков: каналы, терминалы, кассы, агрегаторы.",
      buttonText: "Скачать .xlsx",
      buttonColor: "#3b82f6",
      onClick: () => downloadFile("concentration", () => reports.concentrationExcel(), `risk_concentration_${astanaDateInput()}.xlsx`),
    },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Экспорт и отчётность</h1>
          <p className="page-subtitle">Генерация сводных отчётов для руководства · время: {ASTANA_TIMEZONE_LABEL}</p>
        </div>
      </div>

      {error && (
        <motion.div
          style={{
            background: "rgba(220, 38, 38, 0.1)",
            border: "1px solid rgba(220, 38, 38, 0.3)",
            borderRadius: 12,
            padding: 12,
            marginBottom: 24,
            color: "#dc2626",
            fontSize: "0.875rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center"
          }}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            style={{ background: "none", border: "none", color: "#dc2626", cursor: "pointer", fontSize: "1.2rem" }}
          >
            ✕
          </button>
        </motion.div>
      )}

      <div className="grid-3">
        {/* Suspicious Excel Report */}
        <motion.div
          className="card"
          style={{ padding: 24, gridColumn: "span 1" }}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
            <FileSpreadsheet size={32} style={{ color: "#10b981" }} />
            <button
              className={`btn btn-sm btn-icon ${showFilters ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setShowFilters(!showFilters)}
              title="Фильтры экспорта"
            >
              <Filter size={16} />
            </button>
          </div>
          <h3 style={{ marginBottom: 8 }}>Excel Отчёт (Операции)</h3>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginBottom: 20, lineHeight: 1.5 }}>
            Полный список подозрительных операций с фильтрами. Все даты в отчёте: {ASTANA_TIMEZONE_LABEL}.
          </p>

          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                style={{ overflow: "hidden", marginBottom: 20 }}
              >
                <div style={{ display: "flex", flexDirection: "column", gap: 12, padding: "12px 0", borderTop: "1px solid var(--border)", borderBottom: "1px solid var(--border)" }}>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input className="input" placeholder="Поезд (001Ж)" value={trainNo} onChange={(e) => setTrainNo(e.target.value)} style={{ flex: 1, fontSize: "0.75rem", padding: "6px 10px" }} />
                    <input className="input" placeholder="Касса" value={cashdesk} onChange={(e) => setCashdesk(e.target.value)} style={{ flex: 1, fontSize: "0.75rem", padding: "6px 10px" }} />
                  </div>
                  <input className="input" placeholder="Терминал" value={terminal} onChange={(e) => setTerminal(e.target.value)} style={{ fontSize: "0.75rem", padding: "6px 10px" }} />
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 8 }}>
                    <button type="button" className="btn btn-sm btn-ghost" onClick={() => setQuickRange(7)}>7 дней</button>
                    <button type="button" className="btn btn-sm btn-ghost" onClick={() => setQuickRange(30)}>30 дней</button>
                    <button type="button" className="btn btn-sm btn-ghost" onClick={() => setQuickRange(null)}>Всё</button>
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ fontSize: "0.6875rem", color: "var(--text-muted)", display: "block", marginBottom: 4 }}>Дата с</label>
                      <div style={{ position: "relative" }}>
                        <Calendar size={12} style={{ position: "absolute", left: 8, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
                        <input type="date" className="input" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} style={{ paddingLeft: 26, fontSize: "0.75rem", colorScheme: "dark" }} />
                      </div>
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={{ fontSize: "0.6875rem", color: "var(--text-muted)", display: "block", marginBottom: 4 }}>Дата по</label>
                      <div style={{ position: "relative" }}>
                        <Calendar size={12} style={{ position: "absolute", left: 8, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
                        <input type="date" className="input" value={dateTo} onChange={(e) => setDateTo(e.target.value)} style={{ paddingLeft: 26, fontSize: "0.75rem", colorScheme: "dark" }} />
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <button
            className="btn btn-sm"
            style={{ width: "100%", background: "#10b98114", color: "#10b981", border: "1px solid #10b98130" }}
            onClick={handleDownloadExcel}
            disabled={downloading === "excel"}
          >
            <Download size={14} />
            {downloading === "excel" ? "Загрузка..." : "Скачать .xlsx"}
          </button>
        </motion.div>

        {/* Other Reports */}
        {reportCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.id}
              className="card card-interactive"
              style={{ padding: 24 }}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <Icon size={32} style={{ color: card.color, marginBottom: 16 }} />
              <h3 style={{ marginBottom: 8 }}>{card.title}</h3>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginBottom: 20, lineHeight: 1.5 }}>{card.description}</p>
              <div style={{ flexGrow: 1 }} />
              <button
                className="btn btn-sm"
                style={{ width: "100%", background: `${card.color}14`, color: card.color, border: `1px solid ${card.color}30`, marginTop: "auto" }}
                onClick={card.onClick}
                disabled={downloading === card.id}
              >
                <Download size={14} />
                {downloading === card.id ? "Загрузка..." : card.buttonText}
              </button>
            </motion.div>
          );
        })}

        {/* Passengers Excel Report */}
        <motion.div
          className="card card-interactive"
          style={{ padding: 24, display: "flex", flexDirection: "column" }}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <Users size={32} style={{ color: "#8b5cf6", marginBottom: 16 }} />
          <h3 style={{ marginBottom: 8 }}>Excel по пассажирам</h3>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginBottom: 16, lineHeight: 1.5 }}>
            Выгрузка профилей с risk-score, ML признаками и причинами риска.
          </p>
          <div style={{ flexGrow: 1 }} />
          <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 12 }}>
            <select
              className="input"
              value={passengerRiskBand}
              onChange={(e) => setPassengerRiskBand(e.target.value)}
            >
              <option value="">Все риск-зоны</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <input
              className="input"
              placeholder="ФИО или ИИН"
              value={passengerSearch}
              onChange={(e) => setPassengerSearch(e.target.value)}
            />
          </div>
          <button
            className="btn btn-sm"
            style={{ width: "100%", background: "#8b5cf614", color: "#8b5cf6", border: "1px solid #8b5cf630" }}
            onClick={handleDownloadPassengers}
            disabled={downloading === "passengers"}
          >
            <Download size={14} />
            {downloading === "passengers" ? "Загрузка..." : "Скачать .xlsx"}
          </button>
        </motion.div>

        {/* PDF Report */}
        <motion.div
          className="card card-interactive"
          style={{ padding: 24, display: "flex", flexDirection: "column" }}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <FileText size={32} style={{ color: "#ef4444", marginBottom: 16 }} />
          <h3 style={{ marginBottom: 8 }}>PDF Досье</h3>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginBottom: 16, lineHeight: 1.5 }}>
            Детальная карточка-досье на конкретного пассажира.
          </p>
          <div style={{ flexGrow: 1 }} />
          <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
            <input
              className="input"
              placeholder="ID пассажира"
              value={passengerIdInput}
              onChange={(e) => setPassengerIdInput(e.target.value)}
              style={{ flex: 1 }}
            />
          </div>
          <button
            className="btn btn-sm"
            style={{ width: "100%", background: "#fef2f2", color: "#ef4444", border: "1px solid #fecaca" }}
            onClick={() => {
              if (!passengerIdInput) return;
              downloadFile("pdf", () => reports.passengerPdf(passengerIdInput), `passenger_${passengerIdInput}_dossier.pdf`);
            }}
            disabled={downloading === "pdf" || !passengerIdInput}
          >
            <Download size={14} />
            {downloading === "pdf" ? "Генерация..." : "Сформировать PDF"}
          </button>
        </motion.div>
      </div>
    </div>
  );
}
