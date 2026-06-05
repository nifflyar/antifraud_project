import type {
  LoginRequest,
  RegisterRequest,
  UserProfile,
  ListUsersResponse,
  UserListItem,
  UpdateUserRequest,
  DashboardSummary,
  RiskTrendResponse,
  RiskConcentrationResponse,
  RiskStatsResponse,
  PassengerListResponse,
  PassengerProfile,
  PassengerTransactionsResponse,
  RiskOverrideRequest,
  SuspiciousOperationsResponse,
  UploadListResponse,
  UploadResponse,
  ScoringRunResponse,
  ScoringStatusResponse,
  AuditLogsResponse,
  AuditLogItem,
  RiskBand,
} from "@/types/api";

const BASE = "/api";

function dateStartParam(value?: string): string | undefined {
  if (!value) return undefined;
  return value.includes("T") ? value : `${value}T00:00:00`;
}

function dateEndParam(value?: string): string | undefined {
  if (!value) return undefined;
  return value.includes("T") ? value : `${value}T23:59:59`;
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (res.status === 401) {
    // Try refreshing token
    const refreshRes = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (refreshRes.ok) {
      // Retry original request
      const retryRes = await fetch(`${BASE}${url}`, {
        ...options,
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });
      if (retryRes.ok) {
        if (retryRes.status === 204) return undefined as T;
        return retryRes.json();
      }
    }
    // Refresh also failed — redirect to login
    if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
      window.location.href = "/login";
    }
    throw new ApiError(401, "Not authenticated");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(res.status, body.detail || "API Error");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

async function requestRaw(url: string, options: RequestInit = {}): Promise<Response> {
  const res = await fetch(`${BASE}${url}`, {
    ...options,
    credentials: "include",
  });
  if (res.status === 401 && typeof window !== "undefined") {
    window.location.href = "/login";
  }
  return res;
}

// ============ Auth ============
export const auth = {
  login: (data: LoginRequest) =>
    request<{ success: boolean }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  register: (data: RegisterRequest) =>
    request<{ success: boolean }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  logout: () =>
    request<{ success: boolean }>("/auth/logout", { method: "POST" }),
  refresh: () =>
    request<{ success: boolean }>("/auth/refresh", { method: "POST" }),
};

// ============ Users ============
export const users = {
  me: () => request<UserProfile>("/users/me"),
  list: (limit = 20, offset = 0) =>
    request<ListUsersResponse>(`/users?limit=${limit}&offset=${offset}`),
  getById: (id: number) => request<UserListItem>(`/users/${id}`),
  update: (id: number, data: UpdateUserRequest) =>
    request<UserListItem>(`/users/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id: number) =>
    request<void>(`/users/${id}`, { method: "DELETE" }),
};

// ============ Dashboard ============
export const dashboard = {
  summary: () => request<DashboardSummary>("/dashboard/summary"),
  riskTrend: (dateFrom?: string, dateTo?: string) => {
    const params = new URLSearchParams();
    const from = dateStartParam(dateFrom);
    const to = dateEndParam(dateTo);
    if (from) params.set("date_from", from);
    if (to) params.set("date_to", to);
    const qs = params.toString();
    return request<RiskTrendResponse>(`/dashboard/risk-trend${qs ? `?${qs}` : ""}`);
  },
  riskConcentration: (dimensionType: string, live = false) => {
    const params = new URLSearchParams();
    params.set("dimension_type", dimensionType);
    if (live) params.set("live", "true");
    return request<RiskConcentrationResponse>(
      `/dashboard/risk-concentration?${params.toString()}`
    );
  },
  riskStats: (period?: string, dateFrom?: string, dateTo?: string) => {
    const params = new URLSearchParams();
    if (period) params.set("period", period);
    const from = dateStartParam(dateFrom);
    const to = dateEndParam(dateTo);
    if (from) params.set("date_from", from);
    if (to) params.set("date_to", to);
    const qs = params.toString();
    return request<RiskStatsResponse>(`/dashboard/risk-stats${qs ? `?${qs}` : ""}`);
  },
};

// ============ Passengers ============
export const passengers = {
  list: (params: { risk_band?: RiskBand; search?: string; sort_by?: string; sort_order?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params.risk_band) qs.set("risk_band", params.risk_band);
    if (params.search) qs.set("search", params.search);
    if (params.sort_by) qs.set("sort_by", params.sort_by);
    if (params.sort_order) qs.set("sort_order", params.sort_order);
    qs.set("limit", String(params.limit ?? 50));
    qs.set("offset", String(params.offset ?? 0));
    return request<PassengerListResponse>(`/passengers?${qs.toString()}`);
  },
  getRiskStats: (search?: string) => {
    const qs = new URLSearchParams();
    if (search) qs.set("search", search);
    const query = qs.toString();
    return request<{ critical: number; high: number; medium: number; low: number; unscored?: number; total: number }>(`/passengers/stats/risk-bands${query ? `?${query}` : ""}`);
  },
  getById: (id: string | number) => request<PassengerProfile>(`/passengers/${id}`),
  transactions: (id: string | number, limit = 50, offset = 0) =>
    request<PassengerTransactionsResponse>(
      `/passengers/${id}/transactions?limit=${limit}&offset=${offset}`
    ),
  overrideRisk: (id: string | number, data: RiskOverrideRequest) =>
    request<{ status: string }>(`/passengers/${id}/override`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// ============ Operations ============
export const operations = {
  list: (params: {
    train_no?: string;
    cashdesk?: string;
    terminal?: string;
    channel?: string;
    aggregator?: string;
    point_of_sale?: string;
    op_type?: "sale" | "refund" | "redeem" | "other";
    search?: string;
    date_from?: string;
    date_to?: string;
    sort_by?: "risk_score" | "risk_band" | "final_score" | "date" | "amount" | "train_no" | "passenger";
    sort_order?: "asc" | "desc";
    include_risk_stats?: boolean;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params.train_no) qs.set("train_no", params.train_no);
    if (params.cashdesk) qs.set("cashdesk", params.cashdesk);
    if (params.terminal) qs.set("terminal", params.terminal);
    if (params.channel) qs.set("channel", params.channel);
    if (params.aggregator) qs.set("aggregator", params.aggregator);
    if (params.point_of_sale) qs.set("point_of_sale", params.point_of_sale);
    if (params.op_type) qs.set("op_type", params.op_type);
    if (params.search) qs.set("search", params.search);
    const from = dateStartParam(params.date_from);
    const to = dateEndParam(params.date_to);
    if (from) qs.set("date_from", from);
    if (to) qs.set("date_to", to);
    if (params.sort_by) qs.set("sort_by", params.sort_by);
    if (params.sort_order) qs.set("sort_order", params.sort_order);
    if (params.include_risk_stats) qs.set("include_risk_stats", "true");
    qs.set("limit", String(params.limit ?? 100));
    qs.set("offset", String(params.offset ?? 0));
    return request<SuspiciousOperationsResponse>(
      `/operations?${qs.toString()}`
    );
  },
  suspicious: (params: {
    train_no?: string;
    cashdesk?: string;
    terminal?: string;
    channel?: string;
    aggregator?: string;
    point_of_sale?: string;
    date_from?: string;
    date_to?: string;
    sort_by?: "risk_score" | "risk_band" | "final_score" | "date" | "amount" | "train_no" | "passenger";
    sort_order?: "asc" | "desc";
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params.train_no) qs.set("train_no", params.train_no);
    if (params.cashdesk) qs.set("cashdesk", params.cashdesk);
    if (params.terminal) qs.set("terminal", params.terminal);
    if (params.channel) qs.set("channel", params.channel);
    if (params.aggregator) qs.set("aggregator", params.aggregator);
    if (params.point_of_sale) qs.set("point_of_sale", params.point_of_sale);
    const from = dateStartParam(params.date_from);
    const to = dateEndParam(params.date_to);
    if (from) qs.set("date_from", from);
    if (to) qs.set("date_to", to);
    if (params.sort_by) qs.set("sort_by", params.sort_by);
    if (params.sort_order) qs.set("sort_order", params.sort_order);
    qs.set("limit", String(params.limit ?? 100));
    qs.set("offset", String(params.offset ?? 0));
    return request<SuspiciousOperationsResponse>(
      `/operations/suspicious?${qs.toString()}`
    );
  },
};

// ============ Uploads ============
export const uploads = {
  list: (limit = 20, offset = 0) =>
    request<UploadListResponse>(`/uploads?limit=${limit}&offset=${offset}`),
  getById: (id: number) => request<UploadResponse>(`/uploads/${id}`),
  uploadExcel: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    let res = await fetch(`${BASE}/uploads/excel`, {
      method: "POST",
      body: formData,
      credentials: "include",
    });

    // Handle 401 - token might be expired, try refreshing
    if (res.status === 401) {
      const refreshRes = await fetch(`${BASE}/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });

      if (refreshRes.ok) {
        // Retry upload with new token
        const formData2 = new FormData();
        formData2.append("file", file);
        res = await fetch(`${BASE}/uploads/excel`, {
          method: "POST",
          body: formData2,
          credentials: "include",
        });
      }
    }

    // Still 401 after refresh attempt? Redirect to login
    if (res.status === 401 && typeof window !== "undefined") {
      window.location.href = "/login";
      throw new ApiError(401, "Not authenticated");
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new ApiError(res.status, err.detail);
    }

    return res.json();
  },
};

// ============ Scoring ============
export const scoring = {
  run: (uploadId: number) =>
    request<ScoringRunResponse>("/scoring/run", {
      method: "POST",
      body: JSON.stringify({ upload_id: uploadId }),
    }),
  status: (jobId: string) =>
    request<ScoringStatusResponse>(`/scoring/status/${jobId}`),
};

// ============ Reports ============
export const reports = {
  suspiciousExcel: (params?: {
    train_no?: string;
    cashdesk?: string;
    terminal?: string;
    date_from?: string;
    date_to?: string;
  }) => {
    const qs = new URLSearchParams();
    if (params?.train_no) qs.set("train_no", params.train_no);
    if (params?.cashdesk) qs.set("cashdesk", params.cashdesk);
    if (params?.terminal) qs.set("terminal", params.terminal);
    const from = dateStartParam(params?.date_from);
    const to = dateEndParam(params?.date_to);
    if (from) qs.set("date_from", from);
    if (to) qs.set("date_to", to);
    const query = qs.toString();
    return requestRaw(`/reports/operations/suspicious/excel${query ? `?${query}` : ""}`);
  },
  concentrationExcel: () =>
    requestRaw("/reports/risk-concentration/excel"),
  passengerPdf: (passengerId: string | number) =>
    requestRaw(`/reports/passengers/${String(passengerId)}/pdf`),
  passengersExcel: (params?: { risk_band?: string; search?: string }) => {
    const qs = new URLSearchParams();
    if (params?.risk_band) qs.set("risk_band", params.risk_band);
    if (params?.search) qs.set("search", params.search);
    const query = qs.toString();
    return requestRaw(`/reports/passengers/excel${query ? `?${query}` : ""}`);
  },
};

// ============ Audit ============
export const audit = {
  list: (params?: {
    action?: string;
    user_id?: number;
    entity_type?: string;
    entity_id?: string;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.action) qs.set("action", params.action);
    if (params?.user_id) qs.set("user_id", String(params.user_id));
    if (params?.entity_type) qs.set("entity_type", params.entity_type);
    if (params?.entity_id) qs.set("entity_id", params.entity_id);
    qs.set("limit", String(params?.limit ?? 100));
    qs.set("offset", String(params?.offset ?? 0));
    return request<AuditLogsResponse>(`/audit-logs?${qs.toString()}`).then((res) => ({
      ...res,
      items: res.items ?? res.logs ?? [],
    }));
  },
  getById: (id: string) => request<AuditLogItem>(`/audit-logs/${id}`),
};

// ============ Health ============
export const health = {
  check: () => request<{ status: string }>("/health/"),
};
