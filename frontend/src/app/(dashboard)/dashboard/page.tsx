'use client';

import React, { useState, useEffect } from 'react';
import { TrendingUp, AlertTriangle, Users, BarChart3, RefreshCw, Calendar } from 'lucide-react';
import { motion } from 'framer-motion';
import { dashboard, passengers } from '@/lib/api';
import type { DashboardSummary, RiskStatsResponse, PassengerListItem } from '@/types/api';

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [riskStats, setRiskStats] = useState<RiskStatsResponse | null>(null);
  const [topPassengers, setTopPassengers] = useState<PassengerListItem[]>([]);
  const [period, setPeriod] = useState<'all' | 'today' | 'week' | 'month'>('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [summaryData, statsData, passengersData] = await Promise.all([
        dashboard.summary(),
        dashboard.riskStats(period),
        passengers.list({ risk_band: 'critical', limit: 5 }),
      ]);
      setSummary(summaryData);
      setRiskStats(statsData);
      setTopPassengers(passengersData.items);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [period]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <div style={{ padding: 32, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div className="skeleton" style={{ width: 40, height: 40, borderRadius: '50%' }} />
      </div>
    );
  }

  return (
    <div style={{ padding: 32 }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 className="page-title">RiskGuard Dashboard</h1>
        <p className="page-subtitle">Система мониторинга и детекции подозрительных активностей</p>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24, alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 8 }}>
          {(['all', 'today', 'week', 'month'] as const).map(p => (
            <button
              key={p}
              className={`btn ${period === p ? 'btn-primary' : 'btn-secondary'} btn-sm`}
              onClick={() => setPeriod(p)}
            >
              {p === 'all' ? 'All Time' : p === 'today' ? 'Today' : p === 'week' ? 'This Week' : 'This Month'}
            </button>
          ))}
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={handleRefresh}
          disabled={refreshing}
          style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}
        >
          <RefreshCw size={16} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {/* Summary Stats with Percentages */}
      {summary && (
        <motion.div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 16,
            marginBottom: 32,
          }}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="card" style={{ padding: 20 }}>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: 8 }}>
              Total Passengers
            </p>
            <p className="mono" style={{ fontSize: '2rem', fontWeight: 800, marginBottom: 4 }}>
              {summary.total_passengers.toLocaleString()}
            </p>
          </div>

          <div className="card" style={{ padding: 20, borderLeft: '4px solid var(--risk-critical)' }}>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: 8 }}>
              <AlertTriangle size={16} style={{ display: 'inline', marginRight: 4, color: 'var(--risk-critical)' }} />
              Critical Risk
            </p>
            <p className="mono" style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--risk-critical)', marginBottom: 4 }}>
              {summary.critical_risk_count}
            </p>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              {summary.critical_risk_pct.toFixed(2)}% of passengers
            </p>
          </div>

          <div className="card" style={{ padding: 20, borderLeft: '4px solid var(--risk-high)' }}>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: 8 }}>
              <TrendingUp size={16} style={{ display: 'inline', marginRight: 4, color: 'var(--risk-high)' }} />
              High Risk
            </p>
            <p className="mono" style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--risk-high)', marginBottom: 4 }}>
              {summary.high_risk_count}
            </p>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              {summary.high_risk_pct.toFixed(2)}% of passengers
            </p>
          </div>

          <div className="card" style={{ padding: 20, borderLeft: '4px solid var(--risk-medium)' }}>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: 8 }}>
              <BarChart3 size={16} style={{ display: 'inline', marginRight: 4, color: 'var(--risk-medium)' }} />
              Medium Risk
            </p>
            <p className="mono" style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--risk-medium)', marginBottom: 4 }}>
              {summary.medium_risk_count}
            </p>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              {summary.medium_risk_pct.toFixed(2)}% of passengers
            </p>
          </div>
        </motion.div>
      )}

      {/* Risk Distribution Card */}
      {riskStats && (
        <motion.div className="card" style={{ padding: 24, marginBottom: 32 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: 16 }}>Risk Distribution ({riskStats.period})</h2>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            {[
              { label: 'Critical', count: riskStats.critical_ops, pct: riskStats.critical_pct, color: 'var(--risk-critical)' },
              { label: 'High', count: riskStats.high_ops, pct: riskStats.high_pct, color: 'var(--risk-high)' },
              { label: 'Medium', count: riskStats.medium_ops, pct: riskStats.medium_pct, color: 'var(--risk-medium)' },
              { label: 'Low', count: riskStats.low_ops, pct: riskStats.low_pct, color: 'var(--risk-low)' },
            ].map(stat => (
              <div key={stat.label} style={{ padding: 16, backgroundColor: 'var(--bg-secondary)', borderRadius: 8 }}>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: 8 }}>
                  {stat.label} Operations
                </p>
                <p className="mono" style={{ fontSize: '1.5rem', fontWeight: 800, color: stat.color, marginBottom: 4 }}>
                  {stat.count}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ flex: 1, height: 4, backgroundColor: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ width: `${stat.pct}%`, height: '100%', backgroundColor: stat.color }} />
                  </div>
                  <p style={{ fontSize: '0.8125rem', fontWeight: 600, color: stat.color, minWidth: 40 }}>
                    {stat.pct.toFixed(1)}%
                  </p>
                </div>
              </div>
            ))}
          </div>

          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: 16 }}>
            Total Operations: {riskStats.total_ops.toLocaleString()}
          </p>
        </motion.div>
      )}

      {/* Top Critical Passengers */}
      {topPassengers.length > 0 && (
        <motion.div className="card" style={{ padding: 24 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <AlertTriangle size={20} style={{ color: 'var(--risk-critical)' }} />
            <h2 style={{ fontSize: '1.125rem', fontWeight: 700 }}>Top Critical Passengers</h2>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Passenger ID</th>
                  <th>FIO</th>
                  <th>Risk Score</th>
                  <th>Risk Band</th>
                  <th>Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {topPassengers.map(passenger => (
                  <tr key={passenger.id} style={{ cursor: 'pointer' }} onClick={() => window.location.href = `/passengers/${passenger.id}`}>
                    <td className="mono" style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                      #{passenger.id}
                    </td>
                    <td>{passenger.fio_clean}</td>
                    <td className="mono" style={{ fontWeight: 700, color: 'var(--risk-critical)' }}>
                      {passenger.final_score.toFixed(0)}
                    </td>
                    <td>
                      <span
                        style={{
                          padding: '4px 8px',
                          backgroundColor: 'var(--risk-critical)',
                          color: 'white',
                          borderRadius: 4,
                          fontSize: '0.75rem',
                          fontWeight: 700,
                        }}
                      >
                        {passenger.risk_band.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                      {new Date(passenger.last_seen_at).toLocaleDateString('ru-RU')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </div>
  );
}
