/**
 * Enterprise Dashboard - Main Page
 * Professional fraud detection analytics for large corporations
 * Clean, light theme design
 */

'use client';

import React, { useState, useEffect } from 'react';
import { TrendingUp, AlertTriangle, Users, BarChart3, Download, RefreshCw } from 'lucide-react';
import {
  MetricCard,
  RiskBadge,
  RiskDistributionChart,
  TrendChart,
  FilterBar,
  PassengerTable,
  AlertBanner,
  colorSystem,
  typography
} from '@/components/EnterpriseComponents';

export default function Dashboard() {
  // ========================================================================
  // STATE
  // ========================================================================

  const [filters, setFilters] = useState({
    riskBand: '',
    dateFrom: '',
    dateTo: '',
    channel: ''
  });

  const [loading, setLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(true);
  const [alerts, setAlerts] = useState<Array<{ type: string; title: string; message: string }>>([]);

  // Sample data - replace with actual API calls
  const [dashboard, setDashboard] = useState({
    summary: {
      totalPassengers: 15847,
      criticalRisk: 142,
      highRisk: 1256,
      mediumRisk: 3547,
      lowRisk: 10902,
      highRiskTrend: 8.5,
      criticalRiskTrend: 12.3
    },
    riskDistribution: {
      critical: 142,
      high: 1256,
      medium: 3547,
      low: 10902
    },
    trendData: [
      { date: 'Mon', critical: 12, high: 98, medium: 245, low: 1502 },
      { date: 'Tue', critical: 15, high: 112, medium: 268, low: 1456 },
      { date: 'Wed', critical: 14, high: 108, medium: 252, low: 1478 },
      { date: 'Thu', critical: 18, high: 125, medium: 280, low: 1512 },
      { date: 'Fri', critical: 22, high: 142, medium: 302, low: 1548 },
      { date: 'Sat', critical: 25, high: 156, medium: 318, low: 1602 },
      { date: 'Sun', critical: 20, high: 148, medium: 310, low: 1580 }
    ],
    passengers: [
      {
        id: 'P-2024-001',
        finalScore: 92,
        riskBand: 'critical',
        refundShare: 0.87,
        totalTickets: 156,
        topReasons: ['Быстрые возвраты < 1 часа', 'Скальпирование: 156 билетов']
      },
      {
        id: 'P-2024-002',
        finalScore: 78,
        riskBand: 'high',
        refundShare: 0.65,
        totalTickets: 82,
        topReasons: ['Возвраты < 6 часов до вылета', 'Концентрация билетов']
      },
      {
        id: 'P-2024-003',
        finalScore: 65,
        riskBand: 'high',
        refundShare: 0.58,
        totalTickets: 45,
        topReasons: ['Высокая доля возвратов > 50%', 'Участник подозрительной сети']
      },
      {
        id: 'P-2024-004',
        finalScore: 48,
        riskBand: 'medium',
        refundShare: 0.42,
        totalTickets: 28,
        topReasons: ['Ночные операции > 60%', 'Статистический выброс']
      },
      {
        id: 'P-2024-005',
        finalScore: 35,
        riskBand: 'medium',
        refundShare: 0.38,
        totalTickets: 22,
        topReasons: ['Подозрительное имя', 'Интенсивная активность за 3 дня']
      },
    ]
  });

  // ========================================================================
  // HANDLERS
  // ========================================================================

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleApplyFilters = async () => {
    setLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setLoading(false);
  };

  const handleDownloadReport = () => {
    // Generate and download report
    console.log('Downloading report...');
  };

  const handleRefresh = async () => {
    setDataLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    setDataLoading(false);
    setAlerts([{
      type: 'success',
      title: 'Data Refreshed',
      message: 'Dashboard updated with latest data from ML service'
    }]);
  };

  const handlePassengerClick = (passenger: any) => {
    // Navigate to passenger detail page
    console.log('View passenger:', passenger.id);
  };

  // ========================================================================
  // RENDER
  // ========================================================================

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-primary-50 to-neutral-100">
      {/* ====== HEADER ====== */}
      <header className="bg-white border-b border-neutral-200 sticky top-0 z-40 backdrop-blur-sm bg-opacity-95">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className={`${typography.h2} text-neutral-900`}>
              🛡️ Antifrode Analytics
            </h1>
            <p className={`${typography.bodySmall} text-neutral-500`}>
              Enterprise Fraud Detection Platform
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={handleRefresh}
              disabled={dataLoading}
              className="p-2 hover:bg-neutral-100 rounded-lg transition-colors disabled:opacity-50"
              title="Refresh data"
            >
              <RefreshCw
                size={20}
                className={`text-neutral-600 ${dataLoading ? 'animate-spin' : ''}`}
              />
            </button>
            <button
              onClick={handleDownloadReport}
              className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors font-semibold text-sm"
            >
              <Download size={16} />
              Export Report
            </button>
          </div>
        </div>
      </header>

      {/* ====== MAIN CONTENT ====== */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* ====== ALERTS ====== */}
        {alerts.map((alert, idx) => (
          <AlertBanner
            key={idx}
            type={alert.type}
            title={alert.title}
            message={alert.message}
            onClose={() => setAlerts(alerts.filter((_, i) => i !== idx))}
          />
        ))}

        {/* ====== CRITICAL ALERTS ====== */}
        <AlertBanner
          type="critical"
          title="🚨 Critical Alert: Data Drift Detected"
          message="Model detected unusual pattern shift. Recommendation: Review last 2 days of results. Automatic retraining scheduled for 02:00 UTC."
          onClose={() => { }}
        />

        {/* ====== KPI CARDS ====== */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <MetricCard
            title="Total Passengers"
            value={dashboard.summary.totalPassengers}
            icon={Users}
            status="neutral"
          />
          <MetricCard
            title="Critical Risk"
            value={dashboard.summary.criticalRisk}
            changePercent={dashboard.summary.criticalRiskTrend}
            trend="up"
            icon={AlertTriangle}
            status="critical"
          />
          <MetricCard
            title="High Risk"
            value={dashboard.summary.highRisk}
            changePercent={dashboard.summary.highRiskTrend}
            trend="up"
            icon={TrendingUp}
            status="high"
          />
          <MetricCard
            title="Detection Rate"
            value="92.8%"
            change="+4.2% vs last week"
            icon={BarChart3}
            status="low"
          />
        </section>

        {/* ====== CHARTS ROW ====== */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Risk Distribution */}
          <div className="lg:col-span-1">
            <RiskDistributionChart data={dashboard.riskDistribution} />
          </div>

          {/* Trend Chart */}
          <div className="lg:col-span-2">
            <TrendChart
              title="Risk Trend - Last 7 Days"
              data={dashboard.trendData}
              dataKey="critical"
            />
          </div>
        </section>

        {/* ====== FILTERS ====== */}
        <section className="mb-8">
          <FilterBar
            filters={filters}
            onFilterChange={handleFilterChange}
          />
        </section>

        {/* ====== PASSENGER TABLE ====== */}
        <section className="mb-8">
          <PassengerTable
            passengers={dashboard.passengers}
            onRowClick={handlePassengerClick}
            loading={dataLoading}
          />
        </section>

        {/* ====== INSIGHTS SECTION ====== */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Top Risk Channels */}
          <div className="bg-white rounded-lg border border-neutral-200 shadow-sm p-6">
            <h3 className={`${typography.h4} mb-4 text-neutral-900`}>
              Top Risk Channels
            </h3>
            <div className="space-y-3">
              {[
                { name: 'Terminal #5 (Plaza)', risk: 8.2, transactions: 2345 },
                { name: 'Mobile App', risk: 6.5, transactions: 1854 },
                { name: 'Web Portal', risk: 4.8, transactions: 3021 },
                { name: 'Agent Network', risk: 3.2, transactions: 892 },
              ].map((channel, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg hover:bg-neutral-100 transition-colors">
                  <div className="flex-1">
                    <p className={`${typography.labelMedium} text-neutral-900`}>{channel.name}</p>
                    <p className={`${typography.bodySmall} text-neutral-500`}>{channel.transactions.toLocaleString()} transactions</p>
                  </div>
                  <div className="text-right">
                    <div className="inline-block px-3 py-1 bg-red-100 text-red-700 rounded-full">
                      <span className={`${typography.labelMedium}`}>{channel.risk}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* System Status */}
          <div className="bg-white rounded-lg border border-neutral-200 shadow-sm p-6">
            <h3 className={`${typography.h4} mb-4 text-neutral-900`}>
              System Status
            </h3>
            <div className="space-y-4">
              {[
                { label: 'ML Service', status: 'healthy', latency: '145ms' },
                { label: 'Database', status: 'healthy', latency: '8ms' },
                { label: 'Data Drift', status: 'warning', latency: 'KS=0.042' },
                { label: 'Model Performance', status: 'healthy', latency: 'AUC=0.948' },
              ].map((item, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div>
                    <p className={`${typography.labelMedium} text-neutral-900`}>{item.label}</p>
                    <p className={`${typography.bodySmall} ${item.status === 'healthy' ? 'text-emerald-600' :
                        item.status === 'warning' ? 'text-amber-600' :
                          'text-red-600'
                      }`}>
                      {item.latency}
                    </p>
                  </div>
                  <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${item.status === 'healthy' ? 'bg-emerald-100' :
                      item.status === 'warning' ? 'bg-amber-100' :
                        'bg-red-100'
                    }`}>
                    <span className={`inline-block w-2 h-2 rounded-full ${item.status === 'healthy' ? 'bg-emerald-500' :
                        item.status === 'warning' ? 'bg-amber-500' :
                          'bg-red-500'
                      }`} />
                    <span className={`${typography.bodySmall} ${item.status === 'healthy' ? 'text-emerald-700' :
                        item.status === 'warning' ? 'text-amber-700' :
                          'text-red-700'
                      }`}>
                      {item.status === 'healthy' ? 'Healthy' : item.status === 'warning' ? 'Warning' : 'Critical'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ====== FOOTER INFO ====== */}
        <section className="text-center text-neutral-500 py-8 border-t border-neutral-200">
          <p className={`${typography.bodySmall}`}>
            Last updated: {new Date().toLocaleString()} • ML Model: v2.4.1 • Next sync: in 5 minutes
          </p>
        </section>
      </main>
    </div>
  );
}
