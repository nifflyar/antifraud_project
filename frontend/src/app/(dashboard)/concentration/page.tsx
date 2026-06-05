"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { dashboard } from "@/lib/api";
import type { RiskConcentrationItem } from "@/types/api";
import { ArrowRight, Network, MapPin, CreditCard, Bot } from "lucide-react";
import { motion } from "framer-motion";

const dimensions = [
  { type: "CHANNEL", label: "Каналы", icon: Network, color: "#4f46e5" },
  { type: "TERMINAL", label: "Терминалы", icon: MapPin, color: "#ef4444" },
  { type: "CASHDESK", label: "Кассы", icon: CreditCard, color: "#f97316" },
  { type: "AGGREGATOR", label: "Агрегаторы", icon: Bot, color: "#8b5cf6" },
];

export default function ConcentrationPage() {
  const router = useRouter();
  const [data, setData] = useState<Record<string, RiskConcentrationItem[]>>({});
  const [loading, setLoading] = useState(true);

  const openDimension = (type: string, value: string) => {
    const encoded = encodeURIComponent(value);
    if (type === "TERMINAL") {
      router.push(`/terminals?terminal=${encoded}`);
      return;
    }
    const queryByType: Record<string, string> = {
      CHANNEL: "channel",
      CASHDESK: "cashdesk",
      AGGREGATOR: "aggregator",
    };
    const queryName = queryByType[type];
    if (queryName) {
      router.push(`/operations?${queryName}=${encoded}`);
    }
  };

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      const entries = await Promise.all(
        dimensions.map(async (dim) => {
          try {
            const res = await dashboard.riskConcentration(dim.type);
            return [dim.type, res.items || []] as const;
          } catch {
            return [dim.type, []] as const;
          }
        })
      );
      const results = Object.fromEntries(entries) as Record<string, RiskConcentrationItem[]>;
      setData(results);
      setLoading(false);
    };
    fetchAll();
  }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Анализ концентрации</h1>
          <p className="page-subtitle">Распределение рисков по каналам, терминалам, кассам и агрегаторам</p>
        </div>
      </div>

      <div className="grid-2">
        {dimensions.map((dim, idx) => {
          const items = data[dim.type] || [];
          const Icon = dim.icon;
          return (
            <motion.div
              key={dim.type}
              className="card"
              style={{ padding: 24 }}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
                <div style={{ width: 36, height: 36, borderRadius: "var(--radius-sm)", background: `${dim.color}14`, color: dim.color, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Icon size={18} />
                </div>
                <h3 style={{ fontSize: "0.9375rem" }}>{dim.label}</h3>
              </div>

              {loading ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 36 }} />)}
                </div>
              ) : items.length === 0 ? (
                <div className="empty-state" style={{ padding: 40 }}>
                  <p style={{ fontSize: "0.8125rem" }}>Нет данных</p>
                </div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Имя</th>
                      <th style={{ textAlign: "center" }}>Доля</th>
                      <th style={{ textAlign: "right" }}>Lift</th>
                      <th style={{ textAlign: "right" }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.slice(0, 5).map((item) => {
                      const lift = ((item.lift_vs_base - 1) * 100).toFixed(0);
                      const liftNum = Number(lift);
                      return (
                        <tr
                          key={item.dimension_value}
                          className="clickable"
                          onClick={() => openDimension(dim.type, item.dimension_value)}
                          title="Открыть операции"
                        >
                          <td style={{ fontWeight: 600, fontSize: "0.8125rem" }}>{item.dimension_value}</td>
                          <td style={{ textAlign: "center", color: "var(--text-secondary)", fontSize: "0.8125rem" }}>
                            {(item.share_highrisk_ops * 100).toFixed(1)}%
                          </td>
                          <td className="mono" style={{
                            textAlign: "right",
                            fontWeight: 800,
                            fontSize: "0.8125rem",
                            color: liftNum > 0 ? "var(--risk-critical)" : "var(--risk-low)",
                          }}>
                            {liftNum > 0 ? "+" : ""}{lift}%
                          </td>
                          <td style={{ textAlign: "right", color: "var(--accent)" }}>
                            <ArrowRight size={14} />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
