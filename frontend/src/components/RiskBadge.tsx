"use client";

import React from "react";
import type { RiskBand } from "@/types/api";

const config: Record<RiskBand, string> = {
  low: "badge-low",
  medium: "badge-medium",
  high: "badge-high",
  critical: "badge-critical",
};

export default function RiskBadge({ band }: { band: RiskBand }) {
  return (
    <span className={`badge ${config[band]}`}>
      {band}
    </span>
  );
}
