/**
 * Passenger Detail Page - Individual Fraud Analysis
 * Professional investigation interface for risk officers
 */

'use client';

import React, { useState } from 'react';
import {
  ArrowLeft, MoreVertical, Share2, Flag, MessageSquare,
  Calendar, DollarSign, Train, MapPin, Clock, TrendingUp
} from 'lucide-react';
import { RiskBadge, AlertBanner, colorSystem, typography } from '@/components/EnterpriseComponents';

export default function PassengerDetail() {
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedReason, setExpandedReason] = useState<number | null>(null);

  // Sample data
  const passenger = {
    id: 'P-2024-001',
    name: 'John Doe',
    fio: 'John D.',
    fakeScoreFio: 0.92,
    scores: {
      ruleScore: 58,
      mlScore: 82,
      finalScore: 92,
      riskBand: 'critical'
    },
    features: {
      totalTickets: 156,
      refundCnt: 134,
      refundShare: 0.859,
      nightTickets: 98,
      nightShare: 0.628,
      quickRefunds: 67,
      criticalRefunds: 34,
      activityDays: 8,
      maxTicketsSameDay: 28,
      avgTicketsPerDay: 19.5,
      uniqueTrains: 47,
      uniqueChannels: 3,
      uniqueTerminals: 5,
      inSuspiciousStructure: 1
    },
    topReasons: [
      {
        reason: 'Быстрые возвраты (< 1 часа после покупки)',
        severity: 'critical',
        count: 67,
        details: '67 возвратов совершено в течение 1 часа после покупки. Признак автоматизированного скальпирования.'
      },
      {
        reason: 'Скальпирование: 156 билетов',
        severity: 'critical',
        count: 156,
        details: 'Чрезвычайно высокое количество транзакций от одного пассажира за короткий период.'
      },
      {
        reason: 'Возвраты менее чем за 6 часов до вылета',
        severity: 'critical',
        count: 34,
        details: 'Критичное время возврата - признак попытки переманить билеты после уточнения спроса.'
      },
      {
        reason: 'Ночные операции (> 60%)',
        severity: 'high',
        count: 98,
        details: '62.8% операций приходятся на ночное время - признак автоматизированной системы.'
      },
      {
        reason: 'Участник подозрительной сетевой структуры',
        severity: 'high',
        count: 1,
        details: 'Обнаружено кольцо из 7 пассажиров с одинаковыми кассами и паттернами возвратов.'
      }
    ],
    operations: [
      {
        date: '2024-05-03 02:14:32',
        type: 'sale',
        train: 'TN-2847',
        amount: 145.50,
        channel: 'Mobile',
        terminal: '#5'
      },
      {
        date: '2024-05-03 02:15:18',
        type: 'refund',
        train: 'TN-2847',
        amount: -145.50,
        channel: 'Mobile',
        terminal: '#5'
      },
      {
        date: '2024-05-03 02:45:22',
        type: 'sale',
        train: 'TN-2841',
        amount: 128.00,
        channel: 'Mobile',
        terminal: '#5'
      },
    ],
    firstSeen: '2024-04-25',
    lastSeen: '2024-05-03',
    suspiciousNetwork: [
      { id: 'P-2024-002', name: 'Jane Smith', score: 78 },
      { id: 'P-2024-003', name: 'Alex Johnson', score: 85 },
      { id: 'P-2024-004', name: 'Michael Brown', score: 72 },
    ]
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-primary-50 to-neutral-100">
      {/* ====== HEADER ====== */}
      <header className="bg-white border-b border-neutral-200">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button className="p-2 hover:bg-neutral-100 rounded-lg transition-colors">
              <ArrowLeft size={20} className="text-neutral-600" />
            </button>
            <div>
              <h1 className={`${typography.h2} text-neutral-900`}>
                Passenger Investigation
              </h1>
              <p className={`${typography.bodySmall} text-neutral-500`}>
                ID: {passenger.id}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 hover:bg-neutral-100 rounded-lg transition-colors">
              <Share2 size={20} className="text-neutral-600" />
            </button>
            <button className="p-2 hover:bg-neutral-100 rounded-lg transition-colors">
              <Flag size={20} className="text-neutral-600" />
            </button>
            <button className="p-2 hover:bg-neutral-100 rounded-lg transition-colors">
              <MoreVertical size={20} className="text-neutral-600" />
            </button>
          </div>
        </div>
      </header>

      {/* ====== MAIN CONTENT ====== */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* ====== CRITICAL ALERT ====== */}
        <AlertBanner
          type="critical"
          title="⚠️ Critical Risk Alert"
          message="This passenger exhibits multiple critical fraud indicators. Recommend immediate action: suspend account, investigate network connections, and notify compliance team."
        />

        {/* ====== SCORE CARDS ====== */}
        <section className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {/* Final Score */}
          <div className="bg-white rounded-lg border border-neutral-200 p-6 shadow-sm">
            <p className={`${typography.label} text-neutral-500 mb-2`}>Final Score</p>
            <div className="flex items-end gap-3">
              <div className="flex-1">
                <div className="text-5xl font-bold text-neutral-900">
                  {passenger.scores.finalScore}
                </div>
                <div className="w-full bg-gradient-to-r from-emerald-100 to-red-100 h-1 rounded-full mt-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-emerald-500 to-red-500 h-full"
                    style={{ width: `${passenger.scores.finalScore}%` }}
                  />
                </div>
              </div>
              <div>
                <span className="text-sm font-semibold text-neutral-500">/100</span>
              </div>
            </div>
          </div>

          {/* Rule Score */}
          <div className="bg-white rounded-lg border border-neutral-200 p-6 shadow-sm">
            <p className={`${typography.label} text-neutral-500 mb-2`}>Rule Score</p>
            <p className="text-3xl font-bold text-neutral-900">{passenger.scores.ruleScore}</p>
            <p className={`${typography.bodySmall} text-neutral-500 mt-2`}>
              Domain knowledge
            </p>
          </div>

          {/* ML Score */}
          <div className="bg-white rounded-lg border border-neutral-200 p-6 shadow-sm">
            <p className={`${typography.label} text-neutral-500 mb-2`}>ML Score</p>
            <p className="text-3xl font-bold text-neutral-900">{passenger.scores.mlScore}</p>
            <p className={`${typography.bodySmall} text-neutral-500 mt-2`}>
              Ensemble models
            </p>
          </div>

          {/* Risk Status */}
          <div className="bg-white rounded-lg border border-neutral-200 p-6 shadow-sm flex flex-col justify-center">
            <p className={`${typography.label} text-neutral-500 mb-3`}>Risk Status</p>
            <RiskBadge level={passenger.scores.riskBand} />
          </div>
        </section>

        {/* ====== TABS ====== */}
        <div className="flex gap-8 mb-6 border-b border-neutral-200 bg-white rounded-t-lg px-6">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'reasons', label: 'Risk Factors' },
            { id: 'operations', label: 'Transactions' },
            { id: 'network', label: 'Network Analysis' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-2 font-semibold text-sm border-b-2 transition-colors ${activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-neutral-600 hover:text-neutral-900'
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ====== CONTENT SECTIONS ====== */}
        <div className="bg-white rounded-b-lg border border-neutral-200 border-t-0 p-6">
          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Main Info */}
              <div className="lg:col-span-2">
                <h3 className={`${typography.h4} mb-4 text-neutral-900`}>Passenger Profile</h3>
                <div className="space-y-4">
                  {[
                    { label: 'Name', value: passenger.name },
                    { label: 'FIO Clean', value: passenger.fio },
                    { label: 'Name Authenticity', value: `${(passenger.fakeScoreFio * 100).toFixed(1)}% probability fake` },
                    { label: 'First Seen', value: passenger.firstSeen },
                    { label: 'Last Seen', value: passenger.lastSeen },
                    { label: 'Active Days', value: `${passenger.features.activityDays} days` },
                  ].map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center py-3 border-b border-neutral-100 last:border-0">
                      <span className={`${typography.label} text-neutral-600`}>{item.label}</span>
                      <span className={`${typography.bodyMedium} text-neutral-900 font-semibold`}>{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Key Stats */}
              <div>
                <h3 className={`${typography.h4} mb-4 text-neutral-900`}>Key Statistics</h3>
                <div className="space-y-3">
                  {[
                    { label: 'Total Tickets', value: passenger.features.totalTickets, icon: Train },
                    { label: 'Refund Rate', value: `${(passenger.features.refundShare * 100).toFixed(1)}%`, icon: TrendingUp },
                    { label: 'Night Operations', value: `${(passenger.features.nightShare * 100).toFixed(1)}%`, icon: Clock },
                    { label: 'Unique Routes', value: passenger.features.uniqueTrains, icon: MapPin },
                  ].map((item, idx) => {
                    const Icon = item.icon;
                    return (
                      <div key={idx} className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <Icon size={18} className="text-primary-500" />
                          <span className={`${typography.bodySmall} text-neutral-600`}>{item.label}</span>
                        </div>
                        <span className={`${typography.labelMedium} text-neutral-900`}>{item.value}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* RISK FACTORS TAB */}
          {activeTab === 'reasons' && (
            <div>
              <h3 className={`${typography.h4} mb-6 text-neutral-900`}>Top Risk Factors</h3>
              <div className="space-y-4">
                {passenger.topReasons.map((reason, idx) => (
                  <div
                    key={idx}
                    className={`border rounded-lg transition-all cursor-pointer ${expandedReason === idx
                        ? `bg-gradient-to-r ${reason.severity === 'critical'
                          ? 'from-red-50 to-red-50 border-red-200'
                          : 'from-orange-50 to-orange-50 border-orange-200'
                        }`
                        : 'bg-white border-neutral-200 hover:border-neutral-300'
                      }`}
                    onClick={() => setExpandedReason(expandedReason === idx ? null : idx)}
                  >
                    <div className="p-4 flex items-start gap-4">
                      <div className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${reason.severity === 'critical'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-orange-100 text-orange-700'
                        }`}>
                        {reason.severity === 'critical' ? 'CRITICAL' : 'HIGH'}
                      </div>
                      <div className="flex-1">
                        <h4 className={`${typography.labelMedium} text-neutral-900 mb-1`}>
                          {reason.reason}
                        </h4>
                        {expandedReason === idx && (
                          <p className={`${typography.bodyMedium} text-neutral-600 mt-3`}>
                            {reason.details}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-neutral-900">{reason.count}</div>
                        <p className={`${typography.bodySmall} text-neutral-500`}>occurrences</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TRANSACTIONS TAB */}
          {activeTab === 'operations' && (
            <div>
              <h3 className={`${typography.h4} mb-6 text-neutral-900`}>Recent Transactions</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-neutral-200 bg-neutral-50">
                      <th className={`${typography.label} text-left px-4 py-3`}>Date & Time</th>
                      <th className={`${typography.label} text-left px-4 py-3`}>Type</th>
                      <th className={`${typography.label} text-left px-4 py-3`}>Train</th>
                      <th className={`${typography.label} text-left px-4 py-3`}>Amount</th>
                      <th className={`${typography.label} text-left px-4 py-3`}>Channel</th>
                      <th className={`${typography.label} text-left px-4 py-3`}>Terminal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {passenger.operations.map((op, idx) => (
                      <tr key={idx} className="border-b border-neutral-100 hover:bg-neutral-50">
                        <td className={`${typography.bodySmall} px-4 py-3 text-neutral-600`}>{op.date}</td>
                        <td className={`${typography.bodySmall} px-4 py-3`}>
                          <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${op.type === 'sale'
                              ? 'bg-emerald-100 text-emerald-700'
                              : 'bg-red-100 text-red-700'
                            }`}>
                            {op.type === 'sale' ? 'SALE' : 'REFUND'}
                          </span>
                        </td>
                        <td className={`${typography.bodySmall} px-4 py-3 font-semibold text-neutral-900`}>{op.train}</td>
                        <td className={`${typography.bodySmall} px-4 py-3 text-neutral-900 font-semibold`}>
                          ${Math.abs(op.amount).toFixed(2)}
                        </td>
                        <td className={`${typography.bodySmall} px-4 py-3 text-neutral-600`}>{op.channel}</td>
                        <td className={`${typography.bodySmall} px-4 py-3 text-neutral-600`}>{op.terminal}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* NETWORK TAB */}
          {activeTab === 'network' && (
            <div>
              <h3 className={`${typography.h4} mb-4 text-neutral-900`}>Connected Suspicious Network</h3>
              <p className={`${typography.bodyMedium} text-neutral-600 mb-6`}>
                This passenger is part of a ring of 7 connected accounts with coordinated patterns
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {passenger.suspiciousNetwork.map((member) => (
                  <div key={member.id} className="border border-neutral-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className={`${typography.labelMedium} text-neutral-900`}>{member.name}</h4>
                      <RiskBadge level={member.score > 80 ? 'critical' : member.score > 55 ? 'high' : 'medium'} compact />
                    </div>
                    <div className="flex items-end gap-2">
                      <span className="text-2xl font-bold text-neutral-900">{member.score}</span>
                      <span className={`${typography.bodySmall} text-neutral-500 mb-1`}>/100</span>
                    </div>
                    <button className="mt-3 w-full px-3 py-2 text-primary-600 hover:bg-primary-50 rounded transition-colors text-sm font-semibold">
                      View Profile →
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ====== ACTION BUTTONS ====== */}
        <section className="mt-8 flex gap-4 justify-center">
          <button className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-semibold">
            🚫 Suspend Account
          </button>
          <button className="px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors font-semibold">
            📋 Create Investigation
          </button>
          <button className="px-6 py-3 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors font-semibold">
            💬 Add Note
          </button>
        </section>
      </main>
    </div>
  );
}
