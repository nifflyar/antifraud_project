"use client";

import React, { useEffect, useState, useCallback } from "react";
import { audit } from "@/lib/api";
import type { AuditLogItem } from "@/types/api";
import { useAuth } from "@/lib/auth-context";
import { ScrollText, ChevronLeft, ChevronRight, Shield, Filter, X, Eye, Clock, User, Tag, Hash } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function AuditPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<AuditLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState("");
  const [userIdFilter, setUserIdFilter] = useState("");
  const [entityTypeFilter, setEntityTypeFilter] = useState("");
  const [entityIdFilter, setEntityIdFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState<AuditLogItem | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const limit = 20;

  const fetchData = useCallback(async () => {
    if (!user?.is_admin) { setLoading(false); return; }
    setLoading(true);
    try {
      const res = await audit.list({
        action: actionFilter || undefined,
        user_id: userIdFilter ? parseInt(userIdFilter) : undefined,
        entity_type: entityTypeFilter || undefined,
        entity_id: entityIdFilter || undefined,
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
  }, [page, actionFilter, userIdFilter, entityTypeFilter, entityIdFilter, user]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleViewDetail = async (logItem: AuditLogItem) => {
    setDetailLoading(true);
    setSelectedLog(logItem);
    try {
      const detail = await audit.getById(logItem.id);
      setSelectedLog(detail);
    } catch {
      // If detail fetch fails, still show the list-level data
    } finally {
      setDetailLoading(false);
    }
  };

  const resetFilters = () => {
    setActionFilter("");
    setUserIdFilter("");
    setEntityTypeFilter("");
    setEntityIdFilter("");
    setPage(1);
  };

  const activeFiltersCount = [actionFilter, userIdFilter, entityTypeFilter, entityIdFilter].filter(Boolean).length;

  if (!user?.is_admin) {
    return (
      <div className="empty-state" style={{ minHeight: "60vh" }}>
        <div className="empty-state-icon"><Shield size={28} /></div>
        <p>Эта страница доступна только администраторам</p>
      </div>
    );
  }

  const offset = (page - 1) * limit;

  const actionColor = (action: string) => {
    if (action.includes("LOGIN")) return "var(--info)";
    if (action.includes("LOGOUT")) return "var(--text-muted)";
    if (action.includes("REGISTER")) return "var(--success)";
    if (action.includes("DELETE")) return "var(--error)";
    if (action.includes("UPLOAD")) return "var(--warning)";
    if (action.includes("OVERRIDE")) return "#f97316";
    if (action.includes("SCORING")) return "#8b5cf6";
    return "var(--accent)";
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Аудит логи</h1>
          <p className="page-subtitle">Детальное логирование всех действий пользователей</p>
        </div>
      </div>

      <motion.div className="card" style={{ padding: 24 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        {/* Filters row */}
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-end", gap: 12, marginBottom: 20, paddingBottom: 20, borderBottom: "1px solid var(--border)" }}>
          <div style={{ minWidth: 160 }}>
            <label className="form-label" style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <Filter size={11} /> Действие
            </label>
            <select className="select" value={actionFilter} onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}>
              <option value="">Все действия</option>
              <option value="LOGIN">Вход</option>
              <option value="LOGOUT">Выход</option>
              <option value="USER_CREATED">Регистрация / Создание</option>
              <option value="UPLOAD_COMPLETED">Загрузка файла</option>
              <option value="SCORING_STARTED">Скоринг</option>
              <option value="PASSENGER_RISK_OVERRIDE">Override риска</option>
              <option value="USER_UPDATED">Обновление пользователя</option>
              <option value="USER_DELETED">Удаление пользователя</option>
            </select>
          </div>

          <div style={{ minWidth: 120 }}>
            <label className="form-label" style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <User size={11} /> User ID
            </label>
            <input
              className="input"
              type="number"
              placeholder="ID"
              value={userIdFilter}
              onChange={(e) => { setUserIdFilter(e.target.value); setPage(1); }}
              style={{ width: 100 }}
            />
          </div>

          <div style={{ minWidth: 140 }}>
            <label className="form-label" style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <Tag size={11} /> Тип сущности
            </label>
            <select className="select" value={entityTypeFilter} onChange={(e) => { setEntityTypeFilter(e.target.value); setPage(1); }}>
              <option value="">Все</option>
              <option value="user">user</option>
              <option value="upload">upload</option>
              <option value="passenger">passenger</option>
              <option value="scoring_job">scoring_job</option>
            </select>
          </div>

          <div style={{ minWidth: 140 }}>
            <label className="form-label" style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <Hash size={11} /> Entity ID
            </label>
            <input
              className="input"
              placeholder="ID сущности"
              value={entityIdFilter}
              onChange={(e) => { setEntityIdFilter(e.target.value); setPage(1); }}
              style={{ width: 130 }}
            />
          </div>

          {activeFiltersCount > 0 && (
            <button className="btn btn-ghost btn-sm" onClick={resetFilters} style={{ color: "var(--error)", marginBottom: 2 }}>
              <X size={14} /> Сбросить ({activeFiltersCount})
            </button>
          )}
        </div>

        <div style={{ overflowX: "auto" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Время</th>
                <th>Действие</th>
                <th>Сущность</th>
                <th>Entity ID</th>
                <th>User ID</th>
                <th>Мета</th>
                <th style={{ textAlign: "right" }}>Детали</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                [...Array(6)].map((_, i) => (
                  <tr key={i}>{[...Array(7)].map((__, j) => <td key={j}><div className="skeleton" style={{ width: 80, height: 16 }} /></td>)}</tr>
                ))
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <div className="empty-state">
                      <div className="empty-state-icon"><ScrollText size={28} /></div>
                      <p>{activeFiltersCount > 0 ? "Нет записей по заданным фильтрам" : "Нет записей"}</p>
                      {activeFiltersCount > 0 && (
                        <button className="btn btn-secondary btn-sm" style={{ marginTop: 12 }} onClick={resetFilters}>
                          Сбросить фильтры
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                items.map((log) => (
                  <tr key={log.id} className="clickable" onClick={() => handleViewDetail(log)}>
                    <td style={{ whiteSpace: "nowrap", fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                      {new Date(log.created_at).toLocaleString("ru-RU")}
                    </td>
                    <td>
                      <span className="badge" style={{ background: `${actionColor(log.action)}14`, color: actionColor(log.action) }}>
                        {log.action}
                      </span>
                    </td>
                    <td style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>{log.entity_type || "—"}</td>
                    <td className="mono" style={{ fontSize: "0.8125rem" }}>{log.entity_id || "—"}</td>
                    <td className="mono" style={{ fontSize: "0.8125rem", color: "var(--accent)" }}>{log.user_id || "—"}</td>
                    <td style={{ fontSize: "0.75rem", color: "var(--text-muted)", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {log.meta ? JSON.stringify(log.meta) : "—"}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <button
                        className="btn btn-ghost btn-icon"
                        onClick={(e) => { e.stopPropagation(); handleViewDetail(log); }}
                        title="Просмотр деталей"
                      >
                        <Eye size={15} />
                      </button>
                    </td>
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

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedLog && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedLog(null)}
          >
            <motion.div
              className="modal-content"
              style={{ maxWidth: 600 }}
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                <h3 className="modal-title" style={{ marginBottom: 0 }}>Детали аудит-записи</h3>
                <button className="btn btn-ghost btn-icon" onClick={() => setSelectedLog(null)}><X size={18} /></button>
              </div>

              {detailLoading ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {[...Array(6)].map((_, i) => <div key={i} className="skeleton" style={{ height: 20 }} />)}
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
                  {/* ID */}
                  <div style={{ display: "flex", justifyContent: "space-between", padding: "14px 0", borderBottom: "1px solid var(--border)" }}>
                    <span style={{ color: "var(--text-muted)", fontSize: "0.875rem", fontWeight: 600 }}>ID</span>
                    <span className="mono" style={{ fontSize: "0.8125rem" }}>{selectedLog.id}</span>
                  </div>

                  {/* Timestamp */}
                  <div style={{ display: "flex", justifyContent: "space-between", padding: "14px 0", borderBottom: "1px solid var(--border)" }}>
                    <span style={{ color: "var(--text-muted)", fontSize: "0.875rem", fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}>
                      <Clock size={14} /> Время
                    </span>
                    <span style={{ fontSize: "0.875rem" }}>{new Date(selectedLog.created_at).toLocaleString("ru-RU", { dateStyle: "long", timeStyle: "medium" })}</span>
                  </div>

                  {/* Action */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 0", borderBottom: "1px solid var(--border)" }}>
                    <span style={{ color: "var(--text-muted)", fontSize: "0.875rem", fontWeight: 600 }}>Действие</span>
                    <span className="badge" style={{ background: `${actionColor(selectedLog.action)}14`, color: actionColor(selectedLog.action), fontSize: "0.8125rem" }}>
                      {selectedLog.action}
                    </span>
                  </div>

                  {/* User ID */}
                  <div style={{ display: "flex", justifyContent: "space-between", padding: "14px 0", borderBottom: "1px solid var(--border)" }}>
                    <span style={{ color: "var(--text-muted)", fontSize: "0.875rem", fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}>
                      <User size={14} /> Пользователь
                    </span>
                    <span className="mono" style={{ fontSize: "0.875rem", color: "var(--accent)", fontWeight: 700 }}>
                      {selectedLog.user_id ?? "—"}
                    </span>
                  </div>

                  {/* Entity */}
                  <div style={{ display: "flex", justifyContent: "space-between", padding: "14px 0", borderBottom: "1px solid var(--border)" }}>
                    <span style={{ color: "var(--text-muted)", fontSize: "0.875rem", fontWeight: 600 }}>Сущность</span>
                    <span style={{ fontSize: "0.875rem" }}>
                      {selectedLog.entity_type || "—"}
                      {selectedLog.entity_id && (
                        <span className="mono" style={{ marginLeft: 8, color: "var(--text-secondary)" }}>#{selectedLog.entity_id}</span>
                      )}
                    </span>
                  </div>

                  {/* Meta */}
                  <div style={{ padding: "14px 0" }}>
                    <span style={{ color: "var(--text-muted)", fontSize: "0.875rem", fontWeight: 600, display: "block", marginBottom: 10 }}>Метаданные</span>
                    {selectedLog.meta && Object.keys(selectedLog.meta).length > 0 ? (
                      <div style={{
                        padding: 16,
                        borderRadius: "var(--radius-md)",
                        background: "var(--bg-secondary)",
                        border: "1px solid var(--border)",
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.8125rem",
                        lineHeight: 1.7,
                        whiteSpace: "pre-wrap",
                        wordBreak: "break-all",
                        color: "var(--text-secondary)",
                      }}>
                        {JSON.stringify(selectedLog.meta, null, 2)}
                      </div>
                    ) : (
                      <span style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>Нет метаданных</span>
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
