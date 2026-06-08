"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { passengers as passApi } from "@/lib/api";
import { formatSourceDate, formatSourceDateTime } from "@/lib/datetime";
import type { PassengerProfile, PassengerTransaction, RiskBand } from "@/types/api";
import RiskBadge from "@/components/RiskBadge";
import { useAuth } from "@/lib/auth-context";
import { ArrowLeft, AlertTriangle, Building2, CalendarClock, CheckCircle2, ChevronLeft, ChevronRight, FileText, IdCard, MapPin, Monitor, ShieldAlert, Ticket, TrendingUp, UserRound, Zap } from "lucide-react";
import { motion } from "framer-motion";

interface RiskFeature {
  label: string;
  value: string | number;
  color?: string;
  icon?: React.ReactNode;
}

type RiskReasonSeverity = "critical" | "high" | "medium" | "low";

interface RiskReasonView {
  title: string;
  detail: string;
  category: string;
  severity: RiskReasonSeverity;
}

const riskReasonStyle = (severity: RiskReasonSeverity) => {
  switch (severity) {
    case "critical":
      return { background: "var(--risk-critical-bg)", border: "#fecdd3", color: "var(--risk-critical)" };
    case "high":
      return { background: "var(--risk-high-bg)", border: "#fed7aa", color: "var(--risk-high)" };
    case "medium":
      return { background: "var(--risk-medium-bg)", border: "#fde68a", color: "var(--risk-medium)" };
    default:
      return { background: "var(--bg-secondary)", border: "var(--border)", color: "var(--text-secondary)" };
  }
};

const PASSENGER_LIST_URL_KEY = "riskguard.passengers.returnUrl.v1";
const PASSENGER_LIST_CACHE_KEY = "riskguard.passengers.list.v1";
const PASSENGER_LIST_CACHE_TTL_MS = 10 * 60 * 1000;

const buildPassengerListUrlFromState = (state: Record<string, unknown>): string => {
  const params = new URLSearchParams();
  const search = typeof state.search === "string" ? state.search.trim() : "";
  const riskFilter = typeof state.riskFilter === "string" ? state.riskFilter : "";
  const sortBy = typeof state.sortBy === "string" ? state.sortBy : "";
  const sortOrder = typeof state.sortOrder === "string" ? state.sortOrder : "";
  const page = typeof state.page === "number" ? state.page : Number(state.page || 1);

  if (search) params.set("search", search);
  if (riskFilter) params.set("risk", riskFilter);
  if (sortBy && sortBy !== "risk_band") params.set("sort_by", sortBy);
  if (sortOrder && sortOrder !== "desc") params.set("sort_order", sortOrder);
  if (Number.isFinite(page) && page > 1) params.set("page", String(Math.floor(page)));

  return params.toString() ? `/passengers?${params.toString()}` : "/passengers";
};

const getPassengerListUrl = (): string => {
  if (typeof window === "undefined") return "/passengers";

  try {
    const savedUrl = window.sessionStorage.getItem(PASSENGER_LIST_URL_KEY);
    if (savedUrl?.startsWith("/passengers")) return savedUrl;

    const rawCache = window.sessionStorage.getItem(PASSENGER_LIST_CACHE_KEY);
    if (!rawCache) return "/passengers";
    const cached = JSON.parse(rawCache) as Record<string, unknown>;
    const savedAt = Number(cached.savedAt || 0);
    if (!savedAt || Date.now() - savedAt > PASSENGER_LIST_CACHE_TTL_MS) return "/passengers";
    return buildPassengerListUrlFromState(cached);
  } catch {
    return "/passengers";
  }
};

const formatRiskReason = (reason: string): RiskReasonView => {
  const raw = String(reason || "").trim();
  const lower = raw.toLowerCase();

  const closeRefunds = raw.match(/(\d+)\s+refunds within 24h of departure(?:\s+\((\d+)%\))?/i);
  if (closeRefunds) {
    const count = closeRefunds[1];
    const pct = closeRefunds[2];
    return {
      title: "Возвраты перед отправлением",
      detail: `${count} возвратов сделаны в пределах 24 часов до отправления${pct ? `, это ${pct}% таких возвратов` : ""}. Это сильный сигнал удержания мест или поздней отмены.`,
      category: "Время операции",
      severity: "critical",
    };
  }

  const refundShare = raw.match(/(\d+)%\s+refund share/i);
  if (refundShare) {
    const pct = Number(refundShare[1]);
    return {
      title: "Повышенная доля возвратов",
      detail: `Возвраты составляют ${pct}% операций пассажира. Сервис учитывает это как риск только вместе с другими поведенческими признаками.`,
      category: "Возвраты",
      severity: pct >= 50 ? "high" : "medium",
    };
  }

  const refundCount = raw.match(/^(\d+)\s+refunds$/i);
  if (refundCount) {
    const count = Number(refundCount[1]);
    return {
      title: "Много возвратов",
      detail: `${count} возвратов у одного пассажира. Само по себе это не приговор, но усиливает риск при совпадении по времени, маршруту или суммам.`,
      category: "Возвраты",
      severity: count >= 10 ? "high" : count >= 5 ? "medium" : "low",
    };
  }

  const sameTrain = raw.match(/(\d+)\s+tickets for same train and departure/i);
  if (sameTrain) {
    const count = Number(sameTrain[1]);
    return {
      title: "Концентрация на одном рейсе",
      detail: `${count} билетов связаны с одним поездом и временем отправления. Такой кластер может указывать на удержание мест группой операций.`,
      category: "Seat-blocking",
      severity: count >= 10 ? "high" : "medium",
    };
  }

  const sameDay = raw.match(/(\d+)\s+tickets for same departure day/i);
  if (sameDay) {
    const count = Number(sameDay[1]);
    return {
      title: "Много билетов на одну дату",
      detail: `${count} билетов приходятся на одну дату отправления. Это помогает выявлять массовые или скоординированные действия.`,
      category: "Объём",
      severity: count >= 20 ? "high" : "medium",
    };
  }

  const rapidCancel = raw.match(/(\d+)\s+tickets cancelled within 10 minutes/i);
  if (rapidCancel) {
    const count = Number(rapidCancel[1]);
    return {
      title: "Быстрые отмены",
      detail: `${count} билетов отменены в течение 10 минут после оформления. Это похоже на технический цикл оформления и отмены.`,
      category: "Повторяемость",
      severity: count >= 5 ? "high" : "medium",
    };
  }

  const terminals = raw.match(/operations across (\d+)\s+different terminals/i);
  if (terminals) {
    const count = Number(terminals[1]);
    return {
      title: "Много терминалов",
      detail: `Операции проходили через ${count} разных терминалов. Это не доказывает риск само по себе, но важно при больших объёмах и возвратах.`,
      category: "Концентрация",
      severity: count >= 10 ? "high" : "medium",
    };
  }

  const fioScore = raw.match(/(?:fio pattern appears fake|unusual fio pattern).*score\s+(\d+)\/10/i);
  if (fioScore) {
    const score = Number(fioScore[1]);
    return {
      title: lower.includes("no behavioral corroboration") ? "Подозрительный формат ФИО без подтверждения" : "Подозрительный формат ФИО",
      detail: `Формат имени получил ${score}/10 по признаку искусственного или технического заполнения. Сервис не повышает риск только из-за ФИО без поведенческих сигналов.`,
      category: "Идентичность",
      severity: score >= 8 && !lower.includes("no behavioral corroboration") ? "high" : "medium",
    };
  }

  const nightOps = raw.match(/(\d+)%\s+night operations/i);
  if (nightOps) {
    return {
      title: "Ночная активность",
      detail: `${nightOps[1]}% операций пришлись на ночное время. Это учитывается как дополнительный, а не самостоятельный риск.`,
      category: "Время операции",
      severity: "medium",
    };
  }

  if (lower.includes("strong seat-blocking pattern")) {
    return {
      title: "Сильный паттерн удержания мест",
      detail: "Сочетание объёма, повторяемости и возвратов похоже на сценарий блокировки мест перед отправлением.",
      category: "Seat-blocking",
      severity: "critical",
    };
  }

  if (lower.includes("same_iin_multiple_fio") || lower.includes("identity")) {
    return {
      title: "Расхождение идентификаторов",
      detail: "В скрытых идентификаторах есть несоответствие между пассажирскими данными. Значения не раскрываются в интерфейсе.",
      category: "Идентичность",
      severity: "high",
    };
  }

  return {
    title: "Сигнал риска",
    detail: raw || "Обнаружен дополнительный риск-фактор.",
    category: "Общее",
    severity: "medium",
  };
};

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
  const goBackToPassengerList = () => router.push(getPassengerListUrl());

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
        <button className="btn btn-secondary" style={{ marginTop: 16 }} onClick={goBackToPassengerList}>
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
  const formatDateTime = (value?: string | null) => formatSourceDateTime(value);
  const identityHasConflicts = Boolean(
    identity && (
      identity.distinct_iin_count > 1 ||
      identity.distinct_doc_count > 1 ||
      identity.distinct_phone_count > 1
    )
  );
  const riskReasons = score?.top_reasons.map(formatRiskReason) || [];

  return (
    <div>
      <button className="btn btn-ghost" style={{ marginBottom: 16 }} onClick={goBackToPassengerList}>
        <ArrowLeft size={16} /> Назад к списку
      </button>

      <motion.div className="card" style={{ padding: 32 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 32, paddingBottom: 24, borderBottom: "1px solid var(--border)" }}>
          <div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 800 }}>Пассажир: #{profile.id}</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.125rem", marginTop: 4 }}>ФИО: {profile.fio_clean}</p>
            <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem", marginTop: 4 }}>
              Fake FIO Score: <span className="mono">{profile.fake_fio_score.toFixed(3)}</span> · Первая активность: {formatSourceDate(profile.first_seen_at)}
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
                Обнаружены расхождения в скрытых идентификаторах. Значения ИИН, документов и телефонов не отображаются в интерфейсе.
              </div>
            )}
            <div style={{ marginBottom: 12, padding: 12, borderRadius: "var(--radius-md)", background: "var(--bg-secondary)", border: "1px solid var(--border)", color: "var(--text-secondary)", fontSize: "0.8125rem", display: "flex", gap: 8, alignItems: "center" }}>
              <ShieldAlert size={14} style={{ color: "var(--accent)" }} />
              ИИН, номер документа и телефон скрыты. Сервис использует их только для поиска совпадений и расхождений.
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
              {[
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
                { label: "Разных телефонов", value: String(identity.distinct_phone_count || 0), icon: <ShieldAlert size={16} /> },
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
        {score && riskReasons.length > 0 && (
          <div style={{ marginBottom: 24 }}>
            <h4 style={{ fontSize: "0.6875rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--accent)", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
              <Zap size={14} /> Причины риска
            </h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 12 }}>
              {riskReasons.map((reason, i) => {
                const tone = riskReasonStyle(reason.severity);
                return (
                  <div
                    key={`${reason.title}-${i}`}
                    style={{
                      padding: 14,
                      borderRadius: "var(--radius-md)",
                      background: tone.background,
                      border: `1px solid ${tone.border}`,
                      minWidth: 0,
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "flex-start", marginBottom: 8 }}>
                      <div style={{ display: "flex", gap: 8, alignItems: "center", minWidth: 0 }}>
                        <AlertTriangle size={15} style={{ color: tone.color, flex: "0 0 auto" }} />
                        <p style={{ fontWeight: 800, fontSize: "0.875rem", color: "var(--text-primary)", overflowWrap: "anywhere" }}>
                          {reason.title}
                        </p>
                      </div>
                      <span
                        style={{
                          padding: "3px 7px",
                          borderRadius: 999,
                          background: "rgba(255,255,255,0.65)",
                          border: `1px solid ${tone.border}`,
                          color: tone.color,
                          fontSize: "0.6875rem",
                          fontWeight: 800,
                          whiteSpace: "nowrap",
                        }}
                      >
                        {reason.category}
                      </span>
                    </div>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.8125rem", lineHeight: 1.45 }}>
                      {reason.detail}
                    </p>
                  </div>
                );
              })}
            </div>
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
                  <th>Тариф</th>
                  <th>Класс</th>
                  <th style={{ textAlign: "right" }}>Сумма</th>
                </tr>
              </thead>
              <tbody>
                {txLoading ? (
                  [...Array(5)].map((_, i) => (
                    <tr key={i}>
                      <td colSpan={10} style={{ padding: 0 }}>
                        <div className="skeleton" style={{ height: 40, margin: 0, borderRadius: 0 }} />
                      </td>
                    </tr>
                  ))
                ) : txs.length === 0 ? (
                  <tr><td colSpan={10} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>История пуста</td></tr>
                ) : (
                  txs.map((tx) => (
                    <tr key={tx.id}>
                      <td style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>{formatSourceDateTime(tx.op_datetime)}</td>
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
