"use client";

import React, { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { passengers } from "@/lib/api";
import { formatSourceDate } from "@/lib/datetime";
import type { PassengerListItem, RiskBand } from "@/types/api";
import RiskBadge from "@/components/RiskBadge";
import { Users, Search, ChevronLeft, ChevronRight, Eye, TrendingUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

type PassengerSortBy = "final_score" | "risk_score" | "risk_band" | "date" | "fake_fio" | "name";
type RiskCounts = { critical: number; high: number; medium: number; low: number; unscored: number; total: number };
type PassengerListState = {
  page: number;
  riskFilter: RiskBand | "";
  search: string;
  sortBy: PassengerSortBy;
  sortOrder: "asc" | "desc";
};
type PassengerListCache = PassengerListState & {
  items: PassengerListItem[];
  total: number;
  riskCounts: RiskCounts;
  savedAt: number;
};

const PASSENGER_LIST_CACHE_KEY = "riskguard.passengers.list.v1";
const PASSENGER_LIST_URL_KEY = "riskguard.passengers.returnUrl.v1";
const PASSENGER_LIST_CACHE_TTL_MS = 10 * 60 * 1000;
const DEFAULT_RISK_COUNTS: RiskCounts = { critical: 0, high: 0, medium: 0, low: 0, unscored: 0, total: 0 };

function isRiskBand(value: string | null): value is RiskBand {
  return value === "critical" || value === "high" || value === "medium" || value === "low";
}

function isSortBy(value: string | null): value is PassengerSortBy {
  return value === "final_score" || value === "risk_score" || value === "risk_band" || value === "date" || value === "fake_fio" || value === "name";
}

function isSortOrder(value: string | null): value is "asc" | "desc" {
  return value === "asc" || value === "desc";
}

function readStateFromUrl(): PassengerListState {
  if (typeof window === "undefined") {
    return { page: 1, riskFilter: "", search: "", sortBy: "risk_band", sortOrder: "desc" };
  }

  const params = new URLSearchParams(window.location.search);
  const pageParam = Number(params.get("page") || "1");
  const risk = params.get("risk");
  const sortBy = params.get("sort_by");
  const sortOrder = params.get("sort_order");

  return {
    page: Number.isFinite(pageParam) && pageParam > 0 ? Math.floor(pageParam) : 1,
    riskFilter: isRiskBand(risk) ? risk : "",
    search: params.get("search") || "",
    sortBy: isSortBy(sortBy) ? sortBy : "risk_band",
    sortOrder: isSortOrder(sortOrder) ? sortOrder : "desc",
  };
}

function sameListState(a: PassengerListState, b: PassengerListState): boolean {
  return a.page === b.page
    && a.riskFilter === b.riskFilter
    && a.search === b.search
    && a.sortBy === b.sortBy
    && a.sortOrder === b.sortOrder;
}

function writeStateToUrl(state: PassengerListState): void {
  if (typeof window === "undefined") return;

  const params = new URLSearchParams();
  if (state.search.trim()) params.set("search", state.search.trim());
  if (state.riskFilter) params.set("risk", state.riskFilter);
  if (state.sortBy !== "risk_band") params.set("sort_by", state.sortBy);
  if (state.sortOrder !== "desc") params.set("sort_order", state.sortOrder);
  if (state.page > 1) params.set("page", String(state.page));

  const nextUrl = params.toString() ? `/passengers?${params.toString()}` : "/passengers";
  try {
    window.sessionStorage.setItem(PASSENGER_LIST_URL_KEY, nextUrl);
  } catch {
    // URL state is still present in the address bar.
  }
  if (`${window.location.pathname}${window.location.search}` !== nextUrl) {
    window.history.replaceState(null, "", nextUrl);
  }
}

function readListCache(state: PassengerListState): PassengerListCache | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(PASSENGER_LIST_CACHE_KEY);
    if (!raw) return null;
    const cached = JSON.parse(raw) as PassengerListCache;
    if (!cached.savedAt || Date.now() - cached.savedAt > PASSENGER_LIST_CACHE_TTL_MS) return null;
    if (!Array.isArray(cached.items) || !sameListState(cached, state)) return null;
    return cached;
  } catch {
    return null;
  }
}

function writeListCache(cache: PassengerListCache): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(PASSENGER_LIST_CACHE_KEY, JSON.stringify(cache));
  } catch {
    // Storage can be full or disabled; URL state is still enough to restore filters.
  }
}

function useDebouncedValue<T>(value: T, delay = 350): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}

export default function PassengersPage() {
  const router = useRouter();
  const [items, setItems] = useState<PassengerListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [riskFilter, setRiskFilter] = useState<RiskBand | "">("");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<PassengerSortBy>("risk_band");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [loading, setLoading] = useState(true);
  const [riskCounts, setRiskCounts] = useState<RiskCounts>(DEFAULT_RISK_COUNTS);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const lastLoadedStateRef = useRef<PassengerListState | null>(null);
  const visibleResultRef = useRef({ itemsLength: 0, total: 0 });
  const limit = 20;
  const debouncedSearch = useDebouncedValue(search, 350);

  useEffect(() => {
    visibleResultRef.current = { itemsLength: items.length, total };
  }, [items.length, total]);

  useEffect(() => {
    const restoredState = readStateFromUrl();
    const cached = readListCache(restoredState);

    setPage(restoredState.page);
    setRiskFilter(restoredState.riskFilter);
    setSearch(restoredState.search);
    setSortBy(restoredState.sortBy);
    setSortOrder(restoredState.sortOrder);

    if (cached) {
      setItems(cached.items);
      setTotal(cached.total);
      setRiskCounts(cached.riskCounts || DEFAULT_RISK_COUNTS);
      setLoading(false);
      lastLoadedStateRef.current = restoredState;
    }

    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    writeStateToUrl({ page, riskFilter, search, sortBy, sortOrder });
  }, [hydrated, page, riskFilter, search, sortBy, sortOrder]);

  const fetchRiskStats = useCallback(async () => {
    if (!hydrated) return;
    if (debouncedSearch !== search) return;

    try {
      const stats = await passengers.getRiskStats(debouncedSearch || undefined);
      setRiskCounts({
        critical: stats.critical ?? 0,
        high: stats.high ?? 0,
        medium: stats.medium ?? 0,
        low: stats.low ?? 0,
        unscored: stats.unscored ?? 0,
        total: stats.total ?? 0,
      });
    } catch (err) {
      console.error("Fetch risk stats error:", err);
      setRiskCounts(DEFAULT_RISK_COUNTS);
    }
  }, [hydrated, search, debouncedSearch]);

  const fetchData = useCallback(async () => {
    if (!hydrated) return;
    if (debouncedSearch !== search) return;

    const requestedState: PassengerListState = { page, riskFilter, search, sortBy, sortOrder };
    const hasWarmCache = Boolean(
      lastLoadedStateRef.current
      && sameListState(lastLoadedStateRef.current, requestedState)
      && (visibleResultRef.current.itemsLength > 0 || visibleResultRef.current.total > 0)
    );
    setLoading(!hasWarmCache);
    try {
      const res = await passengers.list({
        risk_band: riskFilter || undefined,
        search: debouncedSearch || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        limit,
        offset: (page - 1) * limit,
      });
      setItems(res.items || []);
      setTotal(res.total || 0);
      lastLoadedStateRef.current = requestedState;
    } catch (err) {
      console.error("Fetch error:", err);
      setItems([]);
      setTotal(0);
      lastLoadedStateRef.current = null;
    } finally {
      setLoading(false);
    }
  }, [hydrated, page, riskFilter, search, debouncedSearch, sortBy, sortOrder]);

  useEffect(() => {
    fetchRiskStats();
  }, [fetchRiskStats]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!hydrated || loading) return;
    if (debouncedSearch !== search) return;
    const currentState: PassengerListState = { page, riskFilter, search, sortBy, sortOrder };
    if (!lastLoadedStateRef.current || !sameListState(lastLoadedStateRef.current, currentState)) return;
    writeListCache({
      page,
      riskFilter,
      search,
      sortBy,
      sortOrder,
      items,
      total,
      riskCounts,
      savedAt: Date.now(),
    });
  }, [hydrated, loading, page, riskFilter, search, debouncedSearch, sortBy, sortOrder, items, total, riskCounts]);

  const offset = (page - 1) * limit;
  const pages = Math.max(1, Math.ceil(total / limit));

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Контроль пассажиров</h1>
          <p className="page-subtitle">Анализ рисков и мониторинг поведения</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 24 }}>
        {[
          { label: "Critical", count: riskCounts.critical, color: "#dc2626" },
          { label: "High", count: riskCounts.high, color: "#ea580c" },
          { label: "Medium", count: riskCounts.medium, color: "#f59e0b" },
          { label: "Low", count: riskCounts.low, color: "#10b981" },
          { label: "Unscored", count: riskCounts.unscored, color: "#94a3b8", filterValue: null },
        ].map(stat => (
          <motion.div
            key={stat.label}
            className="card"
            style={{ padding: 16, cursor: stat.label !== "Unscored" ? "pointer" : "default", opacity: stat.label === "Unscored" ? 0.7 : 1 }}
            whileHover={stat.label !== "Unscored" ? { y: -4 } : {}}
            onClick={() => {
              if (stat.label !== "Unscored") {
                setRiskFilter(stat.label.toLowerCase() as RiskBand);
                setPage(1);
              }
            }}
          >
            <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginBottom: 8 }}>{stat.label}{stat.label !== "Unscored" ? " Risk" : ""}</p>
            <p className="mono" style={{ fontWeight: 800, fontSize: "1.75rem", color: stat.color }}>
              {stat.count}
            </p>
          </motion.div>
        ))}
      </div>

      <motion.div className="card" style={{ padding: 24 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        {/* Filters */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginBottom: 24, justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Users size={20} style={{ color: "var(--accent)" }} />
            <h2 style={{ fontSize: "1.125rem", fontWeight: 700 }}>Список пассажиров ({total})</h2>
          </div>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
            <select className="select" value={riskFilter} onChange={(e) => { setRiskFilter(e.target.value as RiskBand | ""); setPage(1); }}>
              <option value="">Все риски</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select className="select" value={sortBy} onChange={(e) => { setSortBy(e.target.value as PassengerSortBy); setPage(1); }}>
              <option value="risk_band">По уровню риска</option>
              <option value="final_score">По final score</option>
              <option value="risk_score">По risk score</option>
              <option value="date">По дате</option>
              <option value="fake_fio">По подозрению на фейк ФИО</option>
              <option value="name">По имени</option>
            </select>
            <button
              className={`btn ${sortOrder === "desc" ? "btn-primary" : "btn-secondary"} btn-sm`}
              onClick={() => { setSortOrder(sortOrder === "desc" ? "asc" : "desc"); setPage(1); }}
              title={`Сортировка: ${sortOrder === "desc" ? "убывание" : "возрастание"}`}
              style={{ minWidth: 40 }}
            >
              {sortOrder === "desc" ? "↓" : "↑"}
            </button>
            <button
              className={`btn ${showAdvancedFilters ? "btn-primary" : "btn-secondary"} btn-sm`}
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              title="Расширенные фильтры"
            >
              ⚙
            </button>
            <div style={{ position: "relative" }}>
              <Search size={16} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
              <input
                type="text"
                className="input"
                style={{ paddingLeft: 36, width: 260 }}
                placeholder="ФИО, ID, ИИН, документ..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              />
            </div>
          </div>
        </div>

        {/* Advanced Filters Panel */}
        <AnimatePresence>
          {showAdvancedFilters && (
            <motion.div
              style={{ background: "var(--bg-secondary)", padding: 16, borderRadius: 12, marginBottom: 16, border: "1px solid var(--border)" }}
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
            >
              <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginBottom: 12 }}>Расширенные фильтры (для будущих версий API)</p>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
                <div>
                  <label style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Минимальный risk score</label>
                  <input className="input" type="number" placeholder="0-100" style={{ fontSize: "0.875rem" }} disabled />
                </div>
                <div>
                  <label style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Максимальный risk score</label>
                  <input className="input" type="number" placeholder="0-100" style={{ fontSize: "0.875rem" }} disabled />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Table */}
        <div style={{ overflowX: "auto", minHeight: 400 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>ФИО</th>
                <th>Final Score</th>
                <th>Risk Band</th>
                <th>Fake FIO</th>
                <th>Последняя активность</th>
                <th style={{ textAlign: "right" }}>Действия</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i}>
                    <td colSpan={7} style={{ padding: 0 }}>
                      <div className="skeleton" style={{ height: 40, margin: 0, borderRadius: 0 }} />
                    </td>
                  </tr>
                ))
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                    Пассажиры не найдены
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id} style={{ cursor: "pointer" }} onClick={() => router.push(`/passengers/${item.id}`)}>
                    <td className="mono" style={{ fontSize: "0.8125rem", fontWeight: 600 }}>#{item.id}</td>
                    <td style={{ fontWeight: 500 }}>{item.fio_clean}</td>
                    <td className="mono" style={{ fontWeight: 700, color: item.final_score > 75 ? "var(--risk-critical)" : item.final_score > 50 ? "var(--risk-high)" : item.final_score > 30 ? "var(--risk-medium)" : "var(--risk-low)" }}>
                      {item.final_score.toFixed(0)}
                    </td>
                    <td>
                      <RiskBadge band={item.risk_band} />
                    </td>
                    <td className="mono" style={{ fontSize: "0.8125rem", color: item.fake_fio_score > 0.7 ? "var(--risk-high)" : "var(--text-secondary)" }}>
                      {(item.fake_fio_score * 100).toFixed(0)}%
                    </td>
                    <td style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                      {formatSourceDate(item.last_seen_at)}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={(e) => { e.stopPropagation(); router.push(`/passengers/${item.id}`); }}
                      >
                        <Eye size={14} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 24, paddingTop: 24, borderTop: "1px solid var(--border)" }}>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            Показано {offset + 1}–{Math.min(offset + limit, total)} из {total}
          </p>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              className="btn btn-secondary btn-sm"
              disabled={page === 1}
              onClick={() => setPage(Math.max(1, page - 1))}
            >
              <ChevronLeft size={16} /> Назад
            </button>
            <div style={{ display: "flex", alignItems: "center", gap: 8, paddingLeft: 12, paddingRight: 12 }}>
              {[...Array(Math.min(5, pages))].map((_, i) => {
                const p = Math.max(1, page - 2) + i;
                if (p > pages) return null;
                return (
                  <button
                    key={p}
                    className={p === page ? "btn btn-primary btn-sm" : "btn btn-secondary btn-sm"}
                    onClick={() => setPage(p)}
                    style={{ minWidth: 32 }}
                  >
                    {p}
                  </button>
                );
              })}
            </div>
            <button
              className="btn btn-secondary btn-sm"
              disabled={page === pages}
              onClick={() => setPage(Math.min(pages, page + 1))}
            >
              Далее <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
