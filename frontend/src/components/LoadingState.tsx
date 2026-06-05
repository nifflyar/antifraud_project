"use client";

import React, { useEffect, useState } from "react";

interface LoadingStateProps {
  message?: string;
  showTimer?: boolean;
  variant?: "overlay" | "inline" | "skeleton-grid";
  /** Number of skeleton cards to show (for skeleton-grid variant) */
  skeletonCount?: number;
}

/**
 * Premium loading component with elapsed timer.
 * Variants:
 * - "overlay" — centered spinner with message and timer
 * - "inline" — compact inline spinner
 * - "skeleton-grid" — KPI skeleton cards in 3-column grid
 */
export default function LoadingState({
  message = "Загрузка данных",
  showTimer = true,
  variant = "overlay",
  skeletonCount = 6,
}: LoadingStateProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!showTimer) return;
    const start = Date.now();
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [showTimer]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    if (m > 0) return `${m}м ${s.toString().padStart(2, "0")}с`;
    return `${s}с`;
  };

  if (variant === "skeleton-grid") {
    return (
      <div>
        <div className="kpi-grid">
          {[...Array(skeletonCount)].map((_, i) => (
            <div
              key={i}
              className="card skeleton-kpi skeleton"
              style={{
                animationDelay: `${i * 0.15}s`,
              }}
            />
          ))}
        </div>
        {showTimer && (
          <div style={{ textAlign: "center", marginTop: 8 }}>
            <span className="loading-timer">
              Загрузка {formatTime(elapsed)}<span className="loading-dots" />
            </span>
          </div>
        )}
      </div>
    );
  }

  if (variant === "inline") {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "16px 0" }}>
        <div className="loading-spinner" style={{ width: 24, height: 24, borderWidth: 2 }} />
        <span className="loading-text">{message}<span className="loading-dots" /></span>
        {showTimer && elapsed > 0 && (
          <span className="loading-timer">{formatTime(elapsed)}</span>
        )}
      </div>
    );
  }

  // Overlay (default)
  return (
    <div className="loading-overlay">
      <div className="loading-spinner" />
      <div style={{ textAlign: "center" }}>
        <div className="loading-text" style={{ marginBottom: 8 }}>
          {message}<span className="loading-dots" />
        </div>
        {showTimer && (
          <div className="loading-timer">
            Прошло: {formatTime(elapsed)}
          </div>
        )}
      </div>
      <div className="progress-bar-container progress-bar-indeterminate" style={{ maxWidth: 200 }}>
        <div className="progress-bar-fill" />
      </div>
    </div>
  );
}
