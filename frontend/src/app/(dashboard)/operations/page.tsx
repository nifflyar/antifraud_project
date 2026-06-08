"use client";

import React, { useEffect, useState, useCallback } from "react";
import { operations } from "@/lib/api";
import { astanaDateInput, formatSourceDateTime } from "@/lib/datetime";
import type { SuspiciousOperation } from "@/types/api";
import RiskBadge from "@/components/RiskBadge";
import { ArrowLeftRight, ChevronLeft, ChevronRight, Filter, X, Search, Calendar, ArrowUpDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

type OperationSortBy = "risk_score" | "risk_band" | "final_score" | "date" | "amount" | "train_no" | "passenger";

export default function OperationsPage() {
  const [items, setItems] = useState<SuspiciousOperation[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const limit = 20;

  // Filters
  const [trainNo, setTrainNo] = useState("");
  const [cashdesk, setCashdesk] = useState("");
  const [terminal, setTerminal] = useState("");
  const [channel, setChannel] = useState("");
  const [aggregator, setAggregator] = useState("");
  const [pointOfSale, setPointOfSale] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sortBy, setSortBy] = useState<OperationSortBy>("risk_score");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const activeFiltersCount = [trainNo, cashdesk, terminal, channel, aggregator, pointOfSale, dateFrom, dateTo].filter(Boolean).length;

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setTrainNo(params.get("train_no") || "");
    setCashdesk(params.get("cashdesk") || "");
    setTerminal(params.get("terminal") || "");
    setChannel(params.get("channel") || "");
    setAggregator(params.get("aggregator") || "");
    setPointOfSale(params.get("point_of_sale") || "");
  }, []);

  const applyPeriod = (period: "week" | "month" | "quarter" | "all") => {
    if (period === "all") {
      setDateFrom("");
      setDateTo("");
      setPage(1);
      return;
    }
    const now = new Date();
    const days = period === "week" ? 7 : period === "month" ? 30 : 90;
    const from = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
    setDateFrom(astanaDateInput(from));
    setDateTo(astanaDateInput(now));
    setPage(1);
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await operations.suspicious({
        train_no: trainNo || undefined,
        cashdesk: cashdesk || undefined,
        terminal: terminal || undefined,
        channel: channel || undefined,
        aggregator: aggregator || undefined,
        point_of_sale: pointOfSale || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        limit,
        offset: (page - 1) * limit,
      });
      setItems(res.items || []);
      setTotal(res.total || 0);
    } catch {
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, trainNo, cashdesk, terminal, channel, aggregator, pointOfSale, dateFrom, dateTo, sortBy, sortOrder]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const resetFilters = () => {
    setTrainNo("");
    setCashdesk("");
    setTerminal("");
    setChannel("");
    setAggregator("");
    setPointOfSale("");
    setDateFrom("");
    setDateTo("");
    setPage(1);
  };

  const offset = (page - 1) * limit;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Операции высокого риска</h1>
          <p className="page-subtitle">Подозрительные транзакции, выявленные системой</p>
        </div>
        <button
          className={`btn ${showFilters ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter size={16} />
          Фильтры
          {activeFiltersCount > 0 && (
            <span style={{
              background: "var(--accent)",
              color: "#fff",
              borderRadius: "50%",
              width: 20,
              height: 20,
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "0.6875rem",
              fontWeight: 800,
              marginLeft: 4,
            }}>
              {activeFiltersCount}
            </span>
          )}
        </button>
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16, alignItems: "center" }}>
        <button className="btn btn-secondary btn-sm" onClick={() => applyPeriod("week")}>Неделя</button>
        <button className="btn btn-secondary btn-sm" onClick={() => applyPeriod("month")}>Месяц</button>
        <button className="btn btn-secondary btn-sm" onClick={() => applyPeriod("quarter")} >Квартал</button>
        <button className="btn btn-ghost btn-sm" onClick={() => applyPeriod("all")}>Всё время</button>
      </div>

      {/* Filter Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            className="card"
            style={{ padding: 24, marginBottom: 24 }}
            initial={{ opacity: 0, height: 0, marginBottom: 0 }}
            animate={{ opacity: 1, height: "auto", marginBottom: 24 }}
            exit={{ opacity: 0, height: 0, marginBottom: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <Search size={16} style={{ color: "var(--accent)" }} />
                <h3 style={{ fontSize: "0.9375rem", fontWeight: 700 }}>Параметры фильтрации</h3>
              </div>
              {activeFiltersCount > 0 && (
                <button className="btn btn-ghost btn-sm" onClick={resetFilters} style={{ color: "var(--error)" }}>
                  <X size={14} /> Сбросить всё
                </button>
              )}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16 }}>
              <div>
                <label className="form-label">Номер поезда</label>
                <input
                  className="input"
                  placeholder="Например: 001Ж"
                  value={trainNo}
                  onChange={(e) => { setTrainNo(e.target.value); setPage(1); }}
                />
              </div>
              <div>
                <label className="form-label">Касса</label>
                <input
                  className="input"
                  placeholder="Номер кассы"
                  value={cashdesk}
                  onChange={(e) => { setCashdesk(e.target.value); setPage(1); }}
                />
              </div>
              <div>
                <label className="form-label">Терминал</label>
                <input
                  className="input"
                  placeholder="ID терминала"
                  value={terminal}
                  onChange={(e) => { setTerminal(e.target.value); setPage(1); }}
                />
              </div>
              <div>
                <label className="form-label">Канал</label>
                <input
                  className="input"
                  placeholder="Канал продаж"
                  value={channel}
                  onChange={(e) => { setChannel(e.target.value); setPage(1); }}
                />
              </div>
              <div>
                <label className="form-label">Агрегатор</label>
                <input
                  className="input"
                  placeholder="Название агрегатора"
                  value={aggregator}
                  onChange={(e) => { setAggregator(e.target.value); setPage(1); }}
                />
              </div>
              <div>
                <label className="form-label">Пункт продажи</label>
                <input
                  className="input"
                  placeholder="Пункт продажи"
                  value={pointOfSale}
                  onChange={(e) => { setPointOfSale(e.target.value); setPage(1); }}
                />
              </div>
              <div>
                <label className="form-label">
                  <Calendar size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />
                  Дата с
                </label>
                <input
                  className="input"
                  type="date"
                  value={dateFrom}
                  onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
                />
              </div>
              <div>
                <label className="form-label">
                  <Calendar size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />
                  Дата по
                </label>
                <input
                  className="input"
                  type="date"
                  value={dateTo}
                  onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
                />
              </div>
              <div>
                <label className="form-label">
                  <ArrowUpDown size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />
                  Сортировка
                </label>
                <select
                  className="select"
                  value={sortBy}
                  onChange={(e) => { setSortBy(e.target.value as typeof sortBy); setPage(1); }}
                >
                  <option value="risk_score">По риску операции</option>
                  <option value="risk_band">По уровню риска</option>
                  <option value="final_score">По final score пассажира</option>
                  <option value="date">По дате</option>
                  <option value="amount">По сумме</option>
                  <option value="train_no">По поезду</option>
                  <option value="passenger">По пассажиру</option>
                </select>
              </div>
              <div>
                <label className="form-label">Порядок</label>
                <button
                  className={`btn ${sortOrder === "desc" ? "btn-primary" : "btn-secondary"}`}
                  onClick={() => { setSortOrder(sortOrder === "desc" ? "asc" : "desc"); setPage(1); }}
                  style={{ width: "100%", justifyContent: "center" }}
                >
                  {sortOrder === "desc" ? "Убывание" : "Возрастание"}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div className="card" style={{ padding: 24 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
          <ArrowLeftRight size={20} style={{ color: "var(--accent)" }} />
          <h2 style={{ fontSize: "1.125rem" }}>Журнал операций</h2>
          {activeFiltersCount > 0 && (
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 500 }}>
              (фильтров применено: {activeFiltersCount})
            </span>
          )}
        </div>

        <div style={{ overflowX: "auto", minHeight: 400 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Дата/время</th>
                <th>Score</th>
                <th>Причина</th>
                <th>Пассажир ID</th>
                <th>Билет</th>
                <th>ФИО</th>
                <th>Поезд</th>
                <th>Маршрут</th>
                <th>Канал</th>
                <th>Агрегатор</th>
                <th>Терминал</th>
                <th>Пункт продажи</th>
                <th>Тариф</th>
                <th>Класс</th>
                <th>Филиал</th>
                <th>Тип</th>
                <th>Риск</th>
                <th style={{ textAlign: "right" }}>Сумма</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                [...Array(8)].map((_, i) => (
                  <tr key={i}>
                    {[...Array(18)].map((__, j) => (
                      <td key={j}><div className="skeleton" style={{ width: j === 0 ? 120 : 60, height: 16 }} /></td>
                    ))}
                  </tr>
                ))
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={18}>
                    <div className="empty-state">
                      <div className="empty-state-icon"><ArrowLeftRight size={28} /></div>
                      <p>{activeFiltersCount > 0 ? "Нет данных по заданным фильтрам" : "Нет данных"}</p>
                      {activeFiltersCount > 0 && (
                        <button className="btn btn-secondary btn-sm" style={{ marginTop: 12 }} onClick={resetFilters}>
                          Сбросить фильтры
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                items.map((op) => (
                  <tr key={op.id}>
                    <td style={{ whiteSpace: "nowrap", color: "var(--text-secondary)", fontSize: "0.8125rem" }}>{formatSourceDateTime(op.op_datetime)}</td>
                    <td className="mono" style={{ fontWeight: 800, color: op.operation_risk_score >= 85 ? "var(--risk-critical)" : op.operation_risk_score >= 65 ? "var(--risk-high)" : "var(--risk-medium)" }}>
                      {op.operation_risk_score}
                    </td>
                    <td style={{ minWidth: 260, fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                      {op.operation_reasons?.[0] || "—"}
                    </td>
                    <td><span className="mono" style={{ fontWeight: 700, color: "var(--accent)" }}>{op.passenger_id}</span></td>
                    <td className="mono" style={{ fontSize: "0.8125rem" }}>{op.ticket_no || "—"}</td>
                    <td style={{ minWidth: 180, fontSize: "0.8125rem" }}>{op.fio || "—"}</td>
                    <td className="mono" style={{ fontSize: "0.8125rem" }}>{op.train_no || "—"}</td>
                    <td style={{ minWidth: 180, color: "var(--text-muted)", fontSize: "0.8125rem" }}>{op.route || "—"}</td>
                    <td style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>{op.channel || "—"}</td>
                    <td style={{ fontSize: "0.8125rem" }}>{op.aggregator || "—"}</td>
                    <td style={{ fontSize: "0.8125rem" }}>{op.terminal || "—"}</td>
                    <td style={{ fontSize: "0.8125rem" }}>{op.point_of_sale || op.cashdesk || "—"}</td>
                    <td style={{ fontSize: "0.8125rem" }}>{op.tariff_type || "—"}</td>
                    <td style={{ fontSize: "0.8125rem" }}>{op.service_class || "—"}</td>
                    <td style={{ fontSize: "0.8125rem" }}>{op.branch || "—"}</td>
                    <td><span style={{ fontWeight: 800, color: op.op_type === "refund" ? "var(--risk-critical)" : "var(--risk-low)" }}>{op.op_type}</span></td>
                    <td><RiskBadge band={op.risk_band} /></td>
                    <td className="mono" style={{ textAlign: "right", fontWeight: 600 }}>{op.amount.toLocaleString()} ₸</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="pagination">
          <span className="pagination-info">Показано {total > 0 ? offset + 1 : 0}-{Math.min(offset + limit, total)} из {total}</span>
          <div className="pagination-controls">
            <button className="pagination-btn" disabled={page === 1} onClick={() => setPage(page - 1)}><ChevronLeft size={16} /></button>
            <span className="pagination-current">{page}</span>
            <button className="pagination-btn" disabled={offset + limit >= total} onClick={() => setPage(page + 1)}><ChevronRight size={16} /></button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
