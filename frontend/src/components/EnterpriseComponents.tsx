/**
 * Enterprise Design System - Antifrode Analytics Platform
 * Simplified version without external component dependencies
 */

import React from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
  ArrowUpRight, ArrowDownRight, AlertCircle, CheckCircle, TrendingUp
} from 'lucide-react';

// ============================================================================
// COLOR SYSTEM
// ============================================================================

export const colorSystem = {
  primary: {
    50: '#f0f7ff',
    100: '#e0f2fe',
    500: '#0ea5e9',
    600: '#0284c7',
    700: '#0369a1',
  },
  critical: {
    50: '#fef2f2',
    100: '#fee2e2',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
  },
  high: {
    50: '#fff7ed',
    100: '#fed7aa',
    500: '#f97316',
    600: '#ea580c',
    700: '#c2410c',
  },
  medium: {
    50: '#fefce8',
    100: '#fef3c7',
    500: '#eab308',
    600: '#ca8a04',
    700: '#a16207',
  },
  low: {
    50: '#f0fdf4',
    100: '#dcfce7',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
  },
  neutral: {
    0: '#ffffff',
    50: '#fafafa',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
};

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography = {
  h1: 'text-4xl font-bold text-neutral-900 tracking-tight',
  h2: 'text-3xl font-bold text-neutral-800 tracking-tight',
  h3: 'text-2xl font-semibold text-neutral-800',
  h4: 'text-xl font-semibold text-neutral-700',
  h5: 'text-lg font-semibold text-neutral-700',
  bodyLarge: 'text-base text-neutral-700 leading-relaxed',
  bodyMedium: 'text-sm text-neutral-600 leading-relaxed',
  bodySmall: 'text-xs text-neutral-600 leading-relaxed',
  label: 'text-xs font-semibold text-neutral-600 uppercase tracking-wider',
  labelMedium: 'text-sm font-semibold text-neutral-700',
};

// ============================================================================
// METRIC CARD
// ============================================================================

export const MetricCard = ({ title, value, change, changePercent, status = 'neutral', icon: Icon = TrendingUp, trend = 'up' }: { title: string; value: number | string; change?: string; changePercent?: number; status?: string; icon?: any; trend?: string }) => {
  const trendColor = trend === 'up' ? 'text-emerald-600' : 'text-red-600';
  const trendIcon = trend === 'up' ? ArrowUpRight : ArrowDownRight;
  const TrendIcon = trendIcon;

  const statusColors = {
    critical: 'bg-red-50 border-red-100',
    high: 'bg-orange-50 border-orange-100',
    medium: 'bg-amber-50 border-amber-100',
    low: 'bg-emerald-50 border-emerald-100',
    neutral: 'bg-slate-50 border-slate-100',
  };

  return (
    <div className={`${statusColors[status as keyof typeof statusColors] || statusColors.neutral} border-l-4 rounded-lg border shadow-sm hover:shadow-lg transition-all p-6`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className={`${typography.bodySmall} text-neutral-600 mb-1`}>{title}</p>
          <div className="flex items-baseline gap-2">
            <span className={`${typography.h3}`}>{typeof value === 'number' ? value.toLocaleString() : value}</span>
            {changePercent && (
              <span className={`${trendColor} flex items-center gap-1 text-sm font-semibold`}>
                <TrendIcon size={16} />
                {Math.abs(changePercent)}%
              </span>
            )}
          </div>
          {change && <p className={`${typography.bodySmall} text-neutral-500 mt-1`}>{change}</p>}
        </div>
        <div className={`p-3 rounded-lg ${status === 'critical' ? 'bg-red-100' : status === 'high' ? 'bg-orange-100' : status === 'medium' ? 'bg-amber-100' : status === 'low' ? 'bg-emerald-100' : 'bg-slate-100'}`}>
          <Icon size={24} className={status === 'critical' ? 'text-red-600' : status === 'high' ? 'text-orange-600' : status === 'medium' ? 'text-amber-600' : status === 'low' ? 'text-emerald-600' : 'text-slate-600'} />
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// RISK BADGE
// ============================================================================

export const RiskBadge = ({ level, count, compact = false }: { level: string; count?: number; compact?: boolean }) => {
  const styles = {
    critical: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-200', dot: 'bg-red-500', label: 'CRITICAL' },
    high: { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-200', dot: 'bg-orange-500', label: 'HIGH RISK' },
    medium: { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-200', dot: 'bg-amber-500', label: 'MEDIUM' },
    low: { bg: 'bg-emerald-100', text: 'text-emerald-700', border: 'border-emerald-200', dot: 'bg-emerald-500', label: 'LOW' },
  };

  const style = styles[level as keyof typeof styles] || styles.low;

  if (compact) {
    return (
      <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full ${style.bg} ${style.text} text-xs font-semibold`}>
        <span className={`inline-block w-2 h-2 rounded-full ${style.dot}`} />
        {style.label}
      </div>
    );
  }

  return (
    <div className={`flex items-center justify-between p-3 rounded-lg border ${style.bg} ${style.border}`}>
      <div className="flex items-center gap-2">
        <span className={`inline-block w-3 h-3 rounded-full ${style.dot}`} />
        <span className={`${typography.labelMedium} ${style.text}`}>{style.label}</span>
      </div>
      {count !== undefined && <span className={`${typography.h4} ${style.text}`}>{count.toLocaleString()}</span>}
    </div>
  );
};

// ============================================================================
// RISK DISTRIBUTION CHART
// ============================================================================

export const RiskDistributionChart = ({ data }: { data: any }) => {
  const chartData = [
    { name: 'Critical', value: data.critical || 0, fill: colorSystem.critical[500] },
    { name: 'High', value: data.high || 0, fill: colorSystem.high[500] },
    { name: 'Medium', value: data.medium || 0, fill: colorSystem.medium[500] },
    { name: 'Low', value: data.low || 0, fill: colorSystem.low[500] },
  ];

  const total = chartData.reduce((sum, d) => sum + d.value, 0) || 1;

  return (
    <div className="bg-white rounded-lg border border-neutral-200 shadow-sm p-6">
      <h3 className={`${typography.h4} mb-6 text-neutral-900`}>Risk Distribution</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie data={chartData} cx="50%" cy="50%" labelLine={false} label={({ name, value }) => `${name}: ${((value / total) * 100).toFixed(1)}%`} outerRadius={80} fill="#8884d8" dataKey="value">
            {chartData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.fill} />)}
          </Pie>
          <Tooltip formatter={(value: any) => typeof value === 'number' ? value.toLocaleString() : value} contentStyle={{ backgroundColor: colorSystem.neutral[50], border: `1px solid ${colorSystem.neutral[200]}`, borderRadius: '8px' }} />
        </PieChart>
      </ResponsiveContainer>
      <div className="grid grid-cols-4 gap-4 mt-6">
        {chartData.map((item) => (
          <div key={item.name} className="text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <span className="inline-block w-3 h-3 rounded-full" style={{ backgroundColor: item.fill }} />
              <span className={`${typography.bodySmall} text-neutral-600`}>{item.name}</span>
            </div>
            <p className={`${typography.h5} text-neutral-900`}>{item.value.toLocaleString()}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================================================
// TREND CHART
// ============================================================================

export const TrendChart = ({ title, data, dataKey = 'value' }: { title: string; data: any; dataKey?: string }) => {
  return (
    <div className="bg-white rounded-lg border border-neutral-200 shadow-sm p-6">
      <h3 className={`${typography.h4} mb-4 text-neutral-900`}>{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke={colorSystem.neutral[200]} />
          <XAxis dataKey="date" stroke={colorSystem.neutral[400]} />
          <YAxis stroke={colorSystem.neutral[400]} />
          <Tooltip contentStyle={{ backgroundColor: colorSystem.neutral[50], border: `1px solid ${colorSystem.neutral[200]}`, borderRadius: '8px' }} />
          <Legend />
          <Line type="monotone" dataKey={dataKey} stroke={colorSystem.primary[500]} strokeWidth={2} dot={{ fill: colorSystem.primary[500], r: 4 }} activeDot={{ r: 6 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

// ============================================================================
// FILTER BAR
// ============================================================================

export const FilterBar = ({ filters = {}, onFilterChange, options = {} }: { filters?: any; onFilterChange: any; options?: any }) => {
  return (
    <div className="bg-gradient-to-r from-neutral-50 to-neutral-100 border border-neutral-200 rounded-lg p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label className={`${typography.label} mb-2 block`}>Risk Band</label>
          <select value={filters.riskBand || ''} onChange={(e) => onFilterChange('riskBand', e.target.value)} className="w-full px-3 py-2 border border-neutral-300 rounded-lg bg-white text-neutral-700 hover:border-neutral-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent">
            <option value="">All Risks</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <div>
          <label className={`${typography.label} mb-2 block`}>Date From</label>
          <input type="date" value={filters.dateFrom || ''} onChange={(e) => onFilterChange('dateFrom', e.target.value)} className="w-full px-3 py-2 border border-neutral-300 rounded-lg bg-white text-neutral-700 hover:border-neutral-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
        </div>
        <div>
          <label className={`${typography.label} mb-2 block`}>Date To</label>
          <input type="date" value={filters.dateTo || ''} onChange={(e) => onFilterChange('dateTo', e.target.value)} className="w-full px-3 py-2 border border-neutral-300 rounded-lg bg-white text-neutral-700 hover:border-neutral-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
        </div>
        <div>
          <label className={`${typography.label} mb-2 block`}>Channel</label>
          <select value={filters.channel || ''} onChange={(e) => onFilterChange('channel', e.target.value)} className="w-full px-3 py-2 border border-neutral-300 rounded-lg bg-white text-neutral-700 hover:border-neutral-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent">
            <option value="">All Channels</option>
            <option value="online">Online</option>
            <option value="terminal">Terminal</option>
            <option value="agent">Agent</option>
          </select>
        </div>
      </div>
      <div className="flex gap-3 mt-4">
        <button className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors font-semibold text-sm">Apply Filters</button>
        <button className="px-4 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-100 transition-colors font-semibold text-sm">Reset</button>
      </div>
    </div>
  );
};

// ============================================================================
// PASSENGER TABLE
// ============================================================================

export const PassengerTable = ({ passengers = [], onRowClick, loading = false }: { passengers?: any; onRowClick: any; loading?: boolean }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-neutral-200 shadow-sm p-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-neutral-200 shadow-sm overflow-hidden">
      <div className="px-6 pt-6 pb-4">
        <h3 className={`${typography.h4} text-neutral-900 mb-2`}>Suspicious Passengers</h3>
        <p className={`${typography.bodySmall} text-neutral-500`}>{passengers.length.toLocaleString()} passengers found</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-neutral-200 bg-neutral-50">
              <th className={`${typography.label} text-left px-4 py-3 text-neutral-600`}>Passenger ID</th>
              <th className={`${typography.label} text-left px-4 py-3 text-neutral-600`}>Risk Score</th>
              <th className={`${typography.label} text-left px-4 py-3 text-neutral-600`}>Status</th>
              <th className={`${typography.label} text-left px-4 py-3 text-neutral-600`}>Refund Rate</th>
              <th className={`${typography.label} text-left px-4 py-3 text-neutral-600`}>Tickets</th>
              <th className={`${typography.label} text-left px-4 py-3 text-neutral-600`}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {passengers.map((passenger: any) => (
              <tr key={passenger.id} className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors cursor-pointer" onClick={() => onRowClick(passenger)}>
                <td className={`${typography.bodyMedium} text-neutral-900 px-4 py-3 font-semibold`}>#{passenger.id}</td>
                <td className={`${typography.bodyMedium} text-neutral-900 px-4 py-3`}>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-primary-400 to-primary-600 flex items-center justify-center text-white text-xs font-bold">{Math.round(passenger.finalScore)}</div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <RiskBadge level={passenger.riskBand} compact />
                </td>
                <td className={`${typography.bodyMedium} text-neutral-600 px-4 py-3`}>{(passenger.refundShare * 100).toFixed(1)}%</td>
                <td className={`${typography.bodyMedium} text-neutral-600 px-4 py-3`}>{passenger.totalTickets}</td>
                <td className="px-4 py-3">
                  <button className="text-primary-600 hover:text-primary-700 font-semibold text-sm">View Details →</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ============================================================================
// ALERT BANNER
// ============================================================================

export const AlertBanner = ({ type = 'info', title, message, onClose }: { type?: string; title: string; message: string; onClose?: any }) => {
  const styles = {
    critical: { bg: 'bg-red-50 border-red-200', icon: 'text-red-600', title: 'text-red-900', text: 'text-red-800' },
    warning: { bg: 'bg-amber-50 border-amber-200', icon: 'text-amber-600', title: 'text-amber-900', text: 'text-amber-800' },
    info: { bg: 'bg-blue-50 border-blue-200', icon: 'text-blue-600', title: 'text-blue-900', text: 'text-blue-800' },
    success: { bg: 'bg-emerald-50 border-emerald-200', icon: 'text-emerald-600', title: 'text-emerald-900', text: 'text-emerald-800' },
  };

  const style = styles[type as keyof typeof styles];

  return (
    <div className={`${style.bg} border border-l-4 rounded-lg p-4 mb-4 flex items-start gap-3`}>
      <AlertCircle className={`${style.icon} flex-shrink-0 mt-0.5`} size={20} />
      <div className="flex-1">
        <h3 className={`${style.title} font-semibold text-sm`}>{title}</h3>
        <p className={`${style.text} text-sm mt-1`}>{message}</p>
      </div>
      {onClose && <button onClick={onClose} className={`${style.icon} hover:opacity-70 transition-opacity`}>×</button>}
    </div>
  );
};

export default {
  colorSystem,
  typography,
  MetricCard,
  RiskBadge,
  RiskDistributionChart,
  TrendChart,
  FilterBar,
  PassengerTable,
  AlertBanner,
};
