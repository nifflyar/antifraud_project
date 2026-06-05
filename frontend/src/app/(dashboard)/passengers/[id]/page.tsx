"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { passengers as passApi } from "@/lib/api";
import type { PassengerProfile, PassengerTransaction, RiskBand } from "@/types/api";
import RiskBadge from "@/components/RiskBadge";
import { useAuth } from "@/lib/auth-context";
import { ArrowLeft, AlertTriangle, Building2, CalendarClock, CheckCircle2, ChevronLeft, ChevronRight, FileText, IdCard, MapPin, Monitor, Phone, ShieldAlert, Ticket, TrendingUp, UserRound, Zap } from "lucide-react";
import { motion } from "framer-motion";

interface RiskFeature {
  label: string;
  value: string | number;
  color?: string;
  icon?: React.ReactNode;
}

export default function PassengerProfilePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const [profile, setProfile] = useState<PassengerProfile | null>(null);
  const [txs, setTxs] = useState<PassengerTransaction[]>([]);
  const [txTotal, setTxTotal] = useState(0);
  const [txPage, setTxPage] = useState(1);
  const [txLoading, setTxLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showOverride, setShowOverride] = useState(false);
  const [overrideBand, setOverrideBand] = useState<RiskBand>("low");
  const [overrideReason, setOverrideReason] = useState("");
  const txLimit = 30;

  useEffect(() => {
    if (!id) return;
    const fetch = async () => {
      setLoading(true);
      try {
        const p = await passApi.getById(id);
        setProfile(p);
      } catch (e) {
        console.error("Profile fetch error:", e);
      } finally {
        setLoading(false);
      }
    };
    setTxPage(1);
    fetch();
  }, [id]);

  useEffect(() => {
    if (!id) return;
    const fetchTransactions = async () => {
      setTxLoading(true);
      try {
        const offset = (txPage - 1) * txLimit;
        const res = await passApi.transactions(id, txLimit, offset);
        setTxs(res.items || []);
        setTxTotal(res.total || 0);
      } catch (e) {
        console.error("Transactions fetch error:", e);
        setTxs([]);
        setTxTotal(0);
      } finally {
        setTxLoading(false);
      }
    };
    fetchTransactions();
  }, [id, txPage]);

  const handleOverride = async () => {
    if (!id) return;
    try {
      await passApi.overrideRisk(id, { new_risk_band: overrideBand, reason: overrideReason });
      setShowOverride(false);
      const p = await passApi.getById(id);
      setProfile(p);
    } catch (e) {
      console.error("Override error:", e);
    }
  };

  if (loading) {
    return (
      <div>
        <div className="skeleton" style={{ width: 200, height: 32, marginBottom: 24 }} />
        <div className="card" style={{ padding: 32 }}>
          <div className="skeleton" style={{ width: 300, height: 24, marginBottom: 16 }} />
          <div className="skeleton" style={{ width: "100%", height: 200 }} />
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="empty-state" style={{ minHeight: "60vh" }}>
        <div className="empty-state-icon"><AlertTriangle size={28} /></div>
        <p>Пассажир не найден</p>
        <button className="btn btn-secondary" style={{ marginTop: 16 }} onClick={() => router.push("/passengers")}>
          ← Назад к списку
        </button>
      </div>
    );
  }

  const score = profile.score;
  const features = profile.features;
  const txOffset = (txPage - 1) * txLimit;
  const txPages = Math.max(1, Math.ceil(txTotal / txLimit));
  const featureFakeFioScore = features
    ? features.fio_fake_score_max > 1
      ? features.fio_fake_score_max / 10
      : features.fio_fake_score_max
    : 0;

  const riskFeatures: RiskFeature[] = features ? [
    { label: "Всего билетов", value: features.total_tickets, color: features.total_tickets > 30 ? "var(--risk-high)" : "inherit" },
    { label: "Возвратов", value: features.refund_cnt, color: features.refund_cnt > 5 ? "var(--risk-critical)" : "inherit" },
    { label: "Доля возвратов", value: `${(features.refund_share * 100).toFixed(1)}%`, color: features.refund_share > 0.5 ? "var(--risk-critical)" : features.refund_share > 0.3 ? "var(--risk-high)" : "inherit" },
    { label: "Очень поздние возвраты (<6ч)", value: features.very_late_refunds || 0, color: (features.very_late_refunds || 0) > 0 ? "var(--risk-critical)" : "inherit" },
    { label: "Быстрые возвраты (<1ч)", value: features.quick_refunds || 0, color: (features.quick_refunds || 0) > 0 ? "var(--risk-critical)" : "inherit" },
    { label: "Похожие возвраты за день", value: features.suspicious_refund_pattern_cnt || 0, color: (features.suspicious_refund_pattern_cnt || 0) > 0 ? "var(--risk-critical)" : "inherit" },
    { label: "Diversity сумм возврата", value: (features.refund_amount_diversity ?? 1).toFixed(2), color: (features.refund_amount_diversity ?? 1) < 0.15 ? "var(--risk-high)" : "inherit" },
    { label: "Ночных билетов", value: features.night_tickets },
    { label: "Доля ночных", value: `${(features.night_share * 100).toFixed(1)}%` },
    { label: "Дней активности", value: features.activity_days || "—", color: features.activity_days && features.activity_days <= 3 ? "var(--risk-high)" : "inherit" },
    { label: "Подозрительное имя", value: `${(featureFakeFioScore * 100).toFixed(0)}%`, color: featureFakeFioScore > 0.7 ? "var(--risk-high)" : "inherit" },
  ] : [];
  const identity = profile.identity;
  const formatValue = (value?: string | null) => {
    const normalized = value?.trim();
    return normalized ? normalized : "—";
  };
  const formatList = (values?: string[] | null) => {
    if (!values || values.length === 0) return "—";
    return values.slice(0, 4).join(", ");
  };
  const formatDateTime = (value?: string | null) => {
    if (!value) return "—";
    return new Date(value).toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };
  const identityHasConflicts = Boolean(
    identity && (
      identity.distinct_iin_count > 1 ||
      identity.distinct_doc_count > 1 ||
      identity.distinct_phone_count > 1
    )
  );

  return (
    <div>
      <button className="btn btn-ghost" style={{ marginBottom: 16 }} onClick={() => router.push("/passengers")}>
        <ArrowLeft size={16} /> Назад к списку
      </button>

      <motion.div className="card" style={{ padding: 32 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 32, paddingBottom: 24, borderBottom: "1px solid var(--border)" }}>
          <div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 800 }}>Пассажир: #{profile.id}</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.125rem", marginTop: 4 }}>ФИО: {profile.fio_clean}</p>
            <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem", marginTop: 4 }}>
              Fake FIO Score: <span className="mono">{profile.fake_fio_score.toFixed(3)}</span> · Первая активность: {new Date(profile.first_seen_at).toLocaleDateString("ru-RU")}
            </p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            {score && (
              <div style={{
                padding: "12px 24px",
                borderRadius: "var(--radius-lg)",
                background: score.risk_band === "critical" ? "var(--risk-critical-bg)" : score.risk_band === "high" ? "var(--risk-high-bg)" : score.risk_band === "medium" ? "var(--risk-medium-bg)" : "var(--risk-low-bg)",
                display: "flex", alignItems: "center", gap: 12,
              }}>
                <span style={{ fontWeight: 800, fontSize: "1.25rem" }}>
                  {score.final_score.toFixed(0)}/100
                </span>
                <RiskBadge band={score.risk_band} />
              </div>
            )}
            {user?.is_admin && (
              <button className="btn btn-secondary btn-sm" onClick={() => setShowOverride(!showOverride)}>
                <ShieldAlert size={14} /> Override
              </button>
            )}
          </div>
        </div>

        {/* Override Modal */}
        {showOverride && (
          <div style={{ marginBottom: 24, padding: 20, background: "var(--bg-secondary)", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
            <h3 style={{ marginBottom: 12, fontSize: "0.9375rem" }}>Переопределить уровень риска</h3>
            <div style={{ display: "flex", gap: 12, alignItems: "flex-end" }}>
              <div>
                <label className="form-label">Новый уровень</label>
                <select className="select" value={overrideBand} onChange={(e) => setOverrideBand(e.target.value as RiskBand)}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              <div style={{ flex: 1 }}>
                <label className="form-label">Причина</label>
                <input className="input" placeholder="Укажите причину..." value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)} />
              </div>
              <button className="btn btn-primary btn-sm" onClick={handleOverride}>Применить</button>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowOverride(false)}>Отмена</button>
            </div>
          </div>
        )}

        {/* Passenger details */}
        {identity && (
          <div style={{ marginBottom: 24 }}>
            <h4 style={{ fontSize: "0.6875rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
              <IdCard size={14} /> Сведения о пассажире
            </h4>
            {identityHasConflicts && (
              <div style={{ marginBottom: 12, padding: 12, borderRadius: "var(--radius-md)", background: "var(--risk-medium-bg)", border: "1px solid #fde68a", color: "var(--text-primary)", fontSize: "0.8125rem", display: "flex", gap: 8, alignItems: "center" }}>
                <AlertTriangle size={14} style={{ color: "var(--risk-medium)" }} />
                Есть расхождения в идентификаторах: ИИН {identity.distinct_iin_count || 0}, документы {identity.distinct_doc_count || 0}, телефоны {identity.distinct_phone_count || 0}
              </div>
            )}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
              {[
                { label: "ИИН", value: formatValue(identity.iin), icon: <IdCard size={16} /> },
                { label: "№ документа", value: formatValue(identity.doc_no), icon: <FileText size={16} /> },
                { label: "Телефон", value: formatValue(identity.phone), icon: <Phone size={16} /> },
                { label: "Пол", value: formatValue(identity.gender), icon: <UserRound size={16} /> },
                { label: "ФИО из файла", value: formatValue(identity.raw_fio), icon: <UserRound size={16} /> },
                { label: "Период операций", value: `${formatDateTime(identity.first_operation_at)} — ${formatDateTime(identity.last_operation_at)}`, icon: <CalendarClock size={16} /> },
                { label: "Каналы", value: formatList(identity.channels), icon: <Monitor size={16} /> },
                { label: "Терминалы", value: formatList(identity.terminals), icon: <Monitor size={16} /> },
                { label: "Филиалы", value: formatList(identity.branches), icon: <Building2 size={16} /> },
                { label: "Пользователи", value: formatList(identity.sale_users), icon: <UserRound size={16} /> },
                { label: "Маршруты", value: formatList(identity.routes), icon: <MapPin size={16} /> },
                { label: "Поезда", value: formatList(identity.train_numbers), icon: <Ticket size={16} /> },
                { label: "Тарифы", value: formatList(identity.tariff_types), icon: <Ticket size={16} /> },
                { label: "Классы", value: formatList(identity.service_classes), icon: <Ticket size={16} /> },
                { label: "Перевозчики", value: formatList(identity.carriers), icon: <Building2 size={16} /> },
                { label: "Агрегаторы", value: formatList(identity.aggregators), icon: <Monitor size={16} /> },
                { label: "Разных ИИН", value: String(identity.distinct_iin_count || 0), icon: <IdCard size={16} /> },
                { label: "Разных документов", value: String(identity.distinct_doc_count || 0), icon: <FileText size={16} /> },
                { label: "Уникальных терминалов", value: String(identity.distinct_terminal_count || 0), icon: <Monitor size={16} /> },
                { label: "Уникальных маршрутов", value: String(identity.distinct_route_count || 0), icon: <MapPin size={16} /> },
              ].map((item) => (
                <div key={item.label} style={{ padding: 14, background: "var(--bg-secondary)", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8, color: "var(--text-muted)" }}>
                    {item.icon}
                    <p style={{ fontSize: "0.75rem" }}>{item.label}</p>
                  </div>
                  <p className="mono" style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--text-primary)", overflowWrap: "anywhere", lineHeight: 1.35 }}>
                    {item.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Seat blocking indicator */}
        {score && (
          <div style={{
            padding: 20,
            borderRadius: "var(--radius-md)",
            marginBottom: 24,
            background: score.seat_blocking_flag ? "var(--risk-critical-bg)" : "var(--risk-low-bg)",
            border: `1px solid ${score.seat_blocking_flag ? "#fecdd3" : "#bbf7d0"}`,
            display: "flex", alignItems: "center", gap: 16,
          }}>
            {score.seat_blocking_flag ? <AlertTriangle size={28} style={{ color: "var(--risk-critical)" }} /> : <CheckCircle2 size={28} style={{ color: "var(--risk-low)" }} />}
            <div>
              <p style={{ fontWeight: 700, fontSize: "0.9375rem" }}>
                {score.seat_blocking_flag ? "Обнаружен Seat-blocking" : "Аномалий не выявлено"}
              </p>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginTop: 2 }}>
                {score.seat_blocking_flag ? "Зафиксировано удержание мест перед отправлением" : "Признаков удержания мест не обнаружено"}
              </p>
            </div>
          </div>
        )}

        {/* Risk Reasons */}
        {score && score.top_reasons.length > 0 && (
          <div style={{ marginBottom: 24, padding: 20, background: "var(--accent-light)", borderRadius: "var(--radius-md)", border: "1px solid #c7d2fe" }}>
            <h4 style={{ fontSize: "0.6875rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--accent)", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
              <Zap size={14} /> Причины риска
            </h4>
            <ul style={{ listStyle: "none", padding: 0 }}>
              {score.top_reasons.map((r, i) => (
                <li key={i} style={{ padding: "6px 0", fontSize: "0.875rem", color: "var(--text-primary)", display: "flex", alignItems: "center", gap: 8 }}>
                  <AlertTriangle size={14} style={{ color: "var(--accent)" }} /> {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Features Grid */}
        {features && (
          <div style={{ marginBottom: 24 }}>
            <h4 style={{ fontSize: "0.6875rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
              <TrendingUp size={14} /> Ключевые метрики
            </h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
              {riskFeatures.map((feature, i) => (
                <div key={i} style={{ padding: 16, background: "var(--bg-secondary)", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
                  <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginBottom: 8 }}>{feature.label}</p>
                  <p className="mono" style={{ fontWeight: 800, fontSize: "1.25rem", color: feature.color || "var(--text-primary)" }}>
                    {feature.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Score breakdown */}
        {score && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
            <div style={{ padding: 20, background: "var(--bg-secondary)", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
              <h4 style={{ fontSize: "0.6875rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: 12 }}>
                Rule Score
              </h4>
              <p className="mono" style={{ fontWeight: 800, fontSize: "1.75rem", color: "var(--accent)" }}>
                {score.rule_score.toFixed(1)}/100
              </p>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginTop: 8 }}>
                Логика на основе правил
              </p>
            </div>
            <div style={{ padding: 20, background: "var(--bg-secondary)", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
              <h4 style={{ fontSize: "0.6875rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: 12 }}>
                ML Score
              </h4>
              <p className="mono" style={{ fontWeight: 800, fontSize: "1.75rem", color: "#f97316" }}>
                {score.ml_score.toFixed(1)}/100
              </p>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginTop: 8 }}>
                Статистические аномалии
              </p>
            </div>
          </div>
        )}

        {/* Transactions */}
        <div>
          <h4 style={{ fontSize: "0.6875rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: 12 }}>
            История транзакций ({txTotal})
          </h4>
          <div style={{ borderRadius: "var(--radius-md)", border: "1px solid var(--border)", overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Тип</th>
                  <th>Билет</th>
                  <th>Поезд</th>
                  <th>Маршрут</th>
                  <th>Канал</th>
                  <th>Терминал</th>
                  <th>ИИН</th>
                  <th>Документ</th>
                  <th>Телефон</th>
                  <th>Тариф</th>
                  <th>Класс</th>
                  <th style={{ textAlign: "right" }}>Сумма</th>
                </tr>
              </thead>
              <tbody>
                {txLoading ? (
                  [...Array(5)].map((_, i) => (
                    <tr key={i}>
                      <td colSpan={13} style={{ padding: 0 }}>
                        <div className="skeleton" style={{ height: 40, margin: 0, borderRadius: 0 }} />
                      </td>
                    </tr>
                  ))
                ) : txs.length === 0 ? (
                  <tr><td colSpan={13} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>История пуста</td></tr>
                ) : (
                  txs.map((tx) => (
                    <tr key={tx.id}>
                      <td style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>{new Date(tx.op_datetime).toLocaleDateString("ru-RU")}</td>
                      <td>
                        <span style={{ fontWeight: 700, color: tx.op_type === "refund" ? "var(--risk-critical)" : "var(--risk-low)", textTransform: "uppercase", fontSize: "0.75rem" }}>
                          {tx.op_type}
                        </span>
                      </td>
                      <td className="mono" style={{ fontSize: "0.8125rem" }}>{tx.ticket_no || "—"}</td>
                      <td className="mono" style={{ fontSize: "0.8125rem" }}>{tx.train_no || "—"}</td>
                      <td style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>{tx.route || "—"}</td>
                      <td style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>{tx.channel || "—"}</td>
                      <td className="mono" style={{ fontSize: "0.8125rem" }}>
                        {tx.terminal ? (
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm mono"
                            onClick={() => router.push(`/terminals?terminal=${encodeURIComponent(tx.terminal || "")}`)}
                            style={{ padding: "4px 6px", fontSize: "0.75rem", maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis" }}
                            title={`Открыть терминал ${tx.terminal}`}
                          >
                            {tx.terminal}
                          </button>
                        ) : "—"}
                      </td>
                      <td className="mono" style={{ fontSize: "0.8125rem" }}>{tx.iin || "—"}</td>
                      <td className="mono" style={{ fontSize: "0.8125rem" }}>{tx.doc_no || "—"}</td>
                      <td className="mono" style={{ fontSize: "0.8125rem" }}>{tx.phone || "—"}</td>
                      <td style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>{tx.tariff_type || "—"}</td>
                      <td style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>{tx.service_class || "—"}</td>
                      <td className="mono" style={{ textAlign: "right", fontWeight: 600 }}>{tx.amount.toLocaleString()} ₸</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div className="pagination" style={{ marginTop: 16 }}>
            <span className="pagination-info">
              Показано {txTotal > 0 ? txOffset + 1 : 0}-{Math.min(txOffset + txLimit, txTotal)} из {txTotal}
            </span>
            <div className="pagination-controls">
              <button
                className="pagination-btn"
                disabled={txPage === 1 || txLoading}
                onClick={() => setTxPage(Math.max(1, txPage - 1))}
              >
                <ChevronLeft size={16} />
              </button>
              <span className="pagination-current">{txPage} / {txPages}</span>
              <button
                className="pagination-btn"
                disabled={txPage >= txPages || txLoading}
                onClick={() => setTxPage(Math.min(txPages, txPage + 1))}
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
