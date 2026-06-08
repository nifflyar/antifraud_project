"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { dashboard, operations } from "@/lib/api";
import { formatAstanaDateTime } from "@/lib/datetime";
import type { RiskConcentrationItem, SuspiciousOperation, SuspiciousOperationsResponse } from "@/types/api";
import RiskBadge from "@/components/RiskBadge";
import {
  ArrowLeftRight,
  ChevronLeft,
  ChevronRight,
  MapPin,
  Search,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { motion } from "framer-motion";

type OperationSortBy = "risk_score" | "risk_band" | "final_score" | "date" | "amount" | "train_no" | "passenger";
type OperationType = "sale" | "refund" | "redeem" | "other";
type TerminalSortBy = "risk_ops" | "risk_share" | "lift" | "total_ops" | "name";

function useDebouncedValue<T>(value: T, delay = 350): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}

export default function TerminalsPage() {
  const router = useRouter();
  const [terminals, setTerminals] = useState<RiskConcentrationItem[]>([]);
  const [terminalSearch, setTerminalSearch] = useState("");
  const [terminalSortBy, setTerminalSortBy] = useState<TerminalSortBy>("risk_ops");
  const [terminalSortOrder, setTerminalSortOrder] = useState<"asc" | "desc">("desc");
  const [selectedTerminal, setSelectedTerminal] = useState("");
  const [items, setItems] = useState<SuspiciousOperation[]>([]);
  const [total, setTotal] = useState(0);
  const [operationRiskStats, setOperationRiskStats] = useState<SuspiciousOperationsResponse["risk_stats"]>(null);
  const [page, setPage] = useState(1);
  const [loadingTerminals, setLoadingTerminals] = useState(true);
  const [loadingOps, setLoadingOps] = useState(false);
  const [opType, setOpType] = useState<OperationType | "">("");
  const [search, setSearch] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sortBy, setSortBy] = useState<OperationSortBy>("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const limit = 25;
  const debouncedSearch = useDebouncedValue(search, 350);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const terminal = params.get("terminal") || "";
    setSelectedTerminal(terminal);
    setTerminalSearch(terminal);
  }, []);

  useEffect(() => {
    const fetchTerminals = async () => {
      setLoadingTerminals(true);
      try {
        const res = await dashboard.riskConcentration("TERMINAL", true);
        setTerminals(res.items || []);
      } catch {
        setTerminals([]);
      } finally {
        setLoadingTerminals(false);
      }
    };
    fetchTerminals();
  }, []);

  const visibleTerminals = useMemo(() => {
    const q = terminalSearch.trim().toLowerCase();
    const filtered = q
      ? terminals.filter((item) => item.dimension_value.toLowerCase().includes(q))
      : terminals;
    const direction = terminalSortOrder === "desc" ? -1 : 1;
    const valueOf = (item: RiskConcentrationItem): number | string => {
      switch (terminalSortBy) {
        case "risk_share":
          return item.share_highrisk_ops;
        case "lift":
          return item.lift_vs_base;
        case "total_ops":
          return item.total_ops;
        case "name":
          return item.dimension_value.toLowerCase();
        case "risk_ops":
        default:
          return item.highrisk_ops;
      }
    };

    return [...filtered].sort((a, b) => {
      const av = valueOf(a);
      const bv = valueOf(b);
      let result = 0;
      if (typeof av === "string" || typeof bv === "string") {
        result = String(av).localeCompare(String(bv), "ru");
      } else {
        result = av === bv ? 0 : av > bv ? 1 : -1;
      }
      if (result !== 0) return result * direction;
      return b.total_ops - a.total_ops || a.dimension_value.localeCompare(b.dimension_value, "ru");
    });
  }, [terminals, terminalSearch, terminalSortBy, terminalSortOrder]);

  const selectedStats = useMemo(
    () => terminals.find((item) => item.dimension_value === selectedTerminal),
    [terminals, selectedTerminal]
  );

  const selectTerminal = (terminal: string) => {
    setTerminalSearch(terminal);
    if (terminal === selectedTerminal) return;
    setSelectedTerminal(terminal);
    setItems([]);
    setTotal(0);
    setOperationRiskStats(null);
    setPage(1);
    router.push(`/terminals?terminal=${encodeURIComponent(terminal)}`);
  };

  const fetchOperations = useCallback(async () => {
    if (!selectedTerminal) {
      setItems([]);
      setTotal(0);
      setOperationRiskStats(null);
      return;
    }
    setLoadingOps(true);
    try {
      const res = await operations.list({
        terminal: selectedTerminal,
        op_type: opType || undefined,
        search: debouncedSearch || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        include_risk_stats: page === 1,
        limit,
        offset: (page - 1) * limit,
      });
      setItems(res.items || []);
      setTotal(res.total || 0);
      if (res.risk_stats) {
        setOperationRiskStats(res.risk_stats);
        const hasFilters = Boolean(opType || debouncedSearch || dateFrom || dateTo);
        if (!hasFilters) {
          setTerminals((prev) =>
            prev.map((terminal) => {
              if (terminal.dimension_value !== selectedTerminal) return terminal;
              const nextTotal = res.total || 0;
              const nextRiskOps = res.risk_stats?.suspicious ?? 0;
              return {
                ...terminal,
                total_ops: nextTotal,
                highrisk_ops: nextRiskOps,
                share_highrisk_ops: nextTotal ? nextRiskOps / nextTotal : 0,
              };
            })
          );
        }
      }
    } catch {
      setItems([]);
      setTotal(0);
      setOperationRiskStats(null);
    } finally {
      setLoadingOps(false);
    }
  }, [selectedTerminal, opType, debouncedSearch, dateFrom, dateTo, sortBy, sortOrder, page]);

  useEffect(() => {
    fetchOperations();
  }, [fetchOperations]);

  const offset = (page - 1) * limit;
  const pages = Math.max(1, Math.ceil(total / limit));
  const totalOps = selectedTerminal ? (operationRiskStats ? total : selectedStats?.total_ops ?? total) : (selectedStats?.total_ops ?? 0);
  const riskyOps = operationRiskStats?.suspicious ?? selectedStats?.highrisk_ops ?? 0;
  const highCriticalOps = operationRiskStats?.high_critical ?? 0;
  const share = totalOps ? (riskyOps / totalOps) * 100 : 0;
  const lift = selectedStats ? (selectedStats.lift_vs_base - 1) * 100 : 0;
  const hasOperationFilters = Boolean(opType || search || dateFrom || dateTo);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Терминалы</h1>
          <p className="page-subtitle">Операции, риск и концентрация по каждому терминалу</p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 360px) 1fr", gap: 24, alignItems: "start" }}>
        <motion.div className="card" style={{ padding: 20 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
            <MapPin size={18} style={{ color: "var(--accent)" }} />
            <h2 style={{ fontSize: "1rem", fontWeight: 800 }}>Список терминалов</h2>
          </div>
          <div style={{ position: "relative", marginBottom: 14 }}>
            <Search size={15} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input
              className="input"
              placeholder="Поиск терминала"
              value={terminalSearch}
              onChange={(e) => setTerminalSearch(e.target.value)}
              style={{ paddingLeft: 36, paddingRight: terminalSearch ? 38 : undefined, width: "100%" }}
            />
            {terminalSearch && (
              <button
                type="button"
                aria-label="Очистить поиск терминала"
                className="btn btn-ghost"
                onClick={() => setTerminalSearch("")}
                style={{
                  position: "absolute",
                  right: 6,
                  top: "50%",
                  transform: "translateY(-50%)",
                  width: 28,
                  height: 28,
                  minHeight: 28,
                  padding: 0,
                  borderRadius: "var(--radius-sm)",
                }}
              >
                <X size={14} />
              </button>
            )}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8, alignItems: "end", marginBottom: 14 }}>
            <div>
              <label className="form-label">Сортировка</label>
              <select className="select" value={terminalSortBy} onChange={(e) => setTerminalSortBy(e.target.value as TerminalSortBy)}>
                <option value="risk_ops">По риск-операциям</option>
                <option value="risk_share">По доле риска</option>
                <option value="lift">По lift</option>
                <option value="total_ops">По всем операциям</option>
                <option value="name">По названию</option>
              </select>
            </div>
            <button
              type="button"
              className={`btn ${terminalSortOrder === "desc" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setTerminalSortOrder(terminalSortOrder === "desc" ? "asc" : "desc")}
              style={{ minWidth: 44, paddingInline: 12 }}
              title={terminalSortOrder === "desc" ? "Сортировка по убыванию" : "Сортировка по возрастанию"}
            >
              {terminalSortOrder === "desc" ? "↓" : "↑"}
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: "65vh", overflowY: "auto" }}>
            {loadingTerminals ? (
              [...Array(8)].map((_, i) => <div key={i} className="skeleton" style={{ height: 54 }} />)
            ) : visibleTerminals.length === 0 ? (
              <div className="empty-state" style={{ padding: 32 }}>
                <p style={{ fontSize: "0.8125rem" }}>Нет терминалов</p>
              </div>
            ) : (
              visibleTerminals.map((terminal) => {
                const isActive = terminal.dimension_value === selectedTerminal;
                const displayRiskOps = isActive && operationRiskStats ? riskyOps : terminal.highrisk_ops;
                const displayTotalOps = isActive && operationRiskStats ? totalOps : terminal.total_ops;
                const displayShare = displayTotalOps ? (displayRiskOps / displayTotalOps) * 100 : terminal.share_highrisk_ops * 100;
                const displayValue = isActive && loadingOps && !operationRiskStats
                  ? "..."
                  : `${displayRiskOps} / ${displayShare.toFixed(1)}%`;
                return (
                  <button
                    key={terminal.dimension_value}
                    className={`btn ${isActive ? "btn-primary" : "btn-secondary"}`}
                    onClick={() => selectTerminal(terminal.dimension_value)}
                    style={{
                      justifyContent: "space-between",
                      width: "100%",
                      minHeight: 54,
                      gap: 12,
                      textAlign: "left",
                    }}
                  >
                    <span style={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {terminal.dimension_value}
                    </span>
                    <span className="mono" style={{ fontSize: "0.75rem", color: isActive ? "#fff" : displayRiskOps > 0 ? "var(--risk-critical)" : "var(--risk-low)", whiteSpace: "nowrap" }}>
                      {displayValue}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </motion.div>

        <motion.div className="card" style={{ padding: 24 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
            <div>
              <h2 style={{ fontSize: "1.125rem", fontWeight: 800, display: "flex", gap: 10, alignItems: "center" }}>
                <ArrowLeftRight size={20} style={{ color: "var(--accent)" }} />
                {selectedTerminal || "Выберите терминал"}
              </h2>
              <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem", marginTop: 4 }}>
                {selectedTerminal ? "Журнал операций выбранного терминала" : "Слева выберите терминал для просмотра операций"}
              </p>
            </div>
          </div>

          {selectedTerminal && (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12, marginBottom: 20 }}>
                <div style={{ padding: 14, background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: 6 }}>Всего операций</p>
                  <p className="mono" style={{ fontWeight: 800, fontSize: "1.25rem" }}>{totalOps.toLocaleString()}</p>
                </div>
                <div style={{ padding: 14, background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: 6 }}>Рисковые операции</p>
                  <p className="mono" style={{ fontWeight: 800, fontSize: "1.25rem", color: "var(--risk-high)" }}>{riskyOps.toLocaleString()}</p>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.7rem", marginTop: 4 }}>
                    High/Critical: {highCriticalOps.toLocaleString()}
                  </p>
                </div>
                <div style={{ padding: 14, background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: 6 }}>Доля риска</p>
                  <p className="mono" style={{ fontWeight: 800, fontSize: "1.25rem" }}>{share.toFixed(1)}%</p>
                </div>
                <div style={{ padding: 14, background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: 6 }}>{hasOperationFilters ? "Lift терминала" : "Lift"}</p>
                  <p className="mono" style={{ fontWeight: 800, fontSize: "1.25rem", color: lift > 0 ? "var(--risk-critical)" : "var(--risk-low)" }}>
                    {lift > 0 ? "+" : ""}{lift.toFixed(0)}%
                  </p>
                  {hasOperationFilters && (
                    <p style={{ color: "var(--text-muted)", fontSize: "0.7rem", marginTop: 4 }}>без текущих фильтров</p>
                  )}
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, alignItems: "end", marginBottom: 16 }}>
                <div>
                  <label className="form-label">Тип операции</label>
                  <select className="select" value={opType} onChange={(e) => { setOpType(e.target.value as OperationType | ""); setPage(1); }}>
                    <option value="">Все</option>
                    <option value="sale">Продажи</option>
                    <option value="refund">Возвраты</option>
                    <option value="redeem">Гашение</option>
                    <option value="other">Прочие</option>
                  </select>
                </div>
                <div>
                  <label className="form-label">Дата с</label>
                  <input className="input" type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1); }} />
                </div>
                <div>
                  <label className="form-label">Дата по</label>
                  <input className="input" type="date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(1); }} />
                </div>
                <div>
                  <label className="form-label">Поиск</label>
                  <input className="input" placeholder="Билет, ИИН, ФИО" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
                </div>
                <div>
                  <label className="form-label">
                    <SlidersHorizontal size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />
                    Сортировка
                  </label>
                  <select className="select" value={sortBy} onChange={(e) => { setSortBy(e.target.value as OperationSortBy); setPage(1); }}>
                    <option value="date">По дате</option>
                    <option value="risk_score">По риску операции</option>
                    <option value="risk_band">По уровню риска</option>
                    <option value="final_score">По final score пассажира</option>
                    <option value="amount">По сумме</option>
                    <option value="train_no">По поезду</option>
                  </select>
                </div>
                <button className={`btn ${sortOrder === "desc" ? "btn-primary" : "btn-secondary"}`} onClick={() => { setSortOrder(sortOrder === "desc" ? "asc" : "desc"); setPage(1); }}>
                  {sortOrder === "desc" ? "Убывание" : "Возрастание"}
                </button>
              </div>

              <div style={{ overflowX: "auto", minHeight: 420 }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Дата/время</th>
                      <th>Тип</th>
                      <th>Score</th>
                      <th>Риск</th>
                      <th>Пассажир</th>
                      <th>Билет</th>
                      <th>ФИО</th>
                      <th>Поезд</th>
                      <th>Маршрут</th>
                      <th>Канал</th>
                      <th>Пункт</th>
                      <th style={{ textAlign: "right" }}>Сумма</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loadingOps ? (
                      [...Array(8)].map((_, i) => (
                        <tr key={i}>
                          {[...Array(12)].map((__, j) => (
                            <td key={j}><div className="skeleton" style={{ width: j === 0 ? 120 : 70, height: 16 }} /></td>
                          ))}
                        </tr>
                      ))
                    ) : items.length === 0 ? (
                      <tr>
                        <td colSpan={12}>
                          <div className="empty-state">
                            <div className="empty-state-icon"><MapPin size={28} /></div>
                            <p>Нет операций по выбранным условиям</p>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      items.map((op) => (
                        <tr key={op.id}>
                          <td style={{ whiteSpace: "nowrap", color: "var(--text-secondary)", fontSize: "0.8125rem" }}>{formatAstanaDateTime(op.op_datetime)}</td>
                          <td><span style={{ fontWeight: 800, color: op.op_type === "refund" ? "var(--risk-critical)" : "var(--risk-low)" }}>{op.op_type}</span></td>
                          <td className="mono" style={{ fontWeight: 800 }}>{op.operation_risk_score}</td>
                          <td><RiskBadge band={op.risk_band} /></td>
                          <td className="mono" style={{ color: "var(--accent)", fontWeight: 700 }}>{op.passenger_id || "—"}</td>
                          <td className="mono" style={{ fontSize: "0.8125rem" }}>{op.ticket_no || "—"}</td>
                          <td style={{ minWidth: 180, fontSize: "0.8125rem" }}>{op.fio || "—"}</td>
                          <td className="mono" style={{ fontSize: "0.8125rem" }}>{op.train_no || "—"}</td>
                          <td style={{ minWidth: 180, color: "var(--text-muted)", fontSize: "0.8125rem" }}>{op.route || "—"}</td>
                          <td style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>{op.channel || "—"}</td>
                          <td style={{ fontSize: "0.8125rem" }}>{op.point_of_sale || op.cashdesk || "—"}</td>
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
                  <button className="pagination-btn" disabled={page === 1 || loadingOps} onClick={() => setPage(Math.max(1, page - 1))}><ChevronLeft size={16} /></button>
                  <span className="pagination-current">{page} / {pages}</span>
                  <button className="pagination-btn" disabled={page >= pages || loadingOps} onClick={() => setPage(Math.min(pages, page + 1))}><ChevronRight size={16} /></button>
                </div>
              </div>
            </>
          )}
        </motion.div>
      </div>
    </div>
  );
}
