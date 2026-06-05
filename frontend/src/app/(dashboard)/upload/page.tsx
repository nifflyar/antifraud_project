"use client";

import React, { useEffect, useState, useCallback } from "react";
import { uploads, scoring } from "@/lib/api";
import type { UploadResponse, ScoringStatusResponse } from "@/types/api";
import { Upload as UploadIcon, FileSpreadsheet, CheckCircle2, Clock, AlertTriangle, Loader2, Zap, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";

type ActiveUploadStatus = "sending" | "accepted" | "done" | "failed";

type ActiveUpload = {
  key: string;
  filename: string;
  size: number;
  status: ActiveUploadStatus;
  uploadId?: string;
  message: string;
};

const normalizeUploadStatus = (status?: string) => (status || "").toLowerCase();

const isUploadInProgress = (status?: string) => {
  const value = normalizeUploadStatus(status);
  return value === "pending" || value === "processing";
};

const formatFileSize = (bytes: number) => {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 MB";
  const mb = bytes / 1024 / 1024;
  return `${mb.toFixed(mb >= 10 ? 0 : 1)} MB`;
};

export default function UploadPage() {
  const [uploadList, setUploadList] = useState<UploadResponse[]>([]);
  const [activeUploads, setActiveUploads] = useState<ActiveUpload[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");
  const [uploadMsgType, setUploadMsgType] = useState<"success" | "error" | "">("");
  const [scoringJobs, setScoringJobs] = useState<Record<string, ScoringStatusResponse>>({});
  const [loading, setLoading] = useState(true);
  const [dragging, setDragging] = useState(false);

  const fetchUploads = useCallback(async () => {
    setLoading(true);
    try {
      const res = await uploads.list(30, 0);
      setUploadList(res.items);
    } catch (e) {
      console.error("Uploads fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchUploads(); }, [fetchUploads]);

  useEffect(() => {
    const hasActiveHistory = uploadList.some((upload) => isUploadInProgress(upload.status));
    const hasActiveQueue = activeUploads.some((upload) => upload.status === "sending" || upload.status === "accepted");
    if (!hasActiveHistory && !hasActiveQueue) return;

    const interval = window.setInterval(() => {
      fetchUploads();
    }, 3000);

    return () => window.clearInterval(interval);
  }, [activeUploads, fetchUploads, uploadList]);

  useEffect(() => {
    if (uploadList.length === 0) return;

    setActiveUploads((prev) =>
      prev.map((item) => {
        if (!item.uploadId) return item;
        const current = uploadList.find((upload) => upload.id === item.uploadId);
        if (!current) return item;

        const status = normalizeUploadStatus(current.status);
        if (status === "done") {
          return { ...item, status: "done", message: "Готово: данные загружены" };
        }
        if (status === "failed") {
          return { ...item, status: "failed", message: "Ошибка обработки файла" };
        }
        if (status === "processing") {
          return { ...item, status: "accepted", message: "Обработка строк..." };
        }
        return { ...item, status: "accepted", message: "Файл принят, ожидает обработки" };
      })
    );
  }, [uploadList]);

  const handleFiles = async (files: FileList | File[]) => {
    const list = Array.from(files);
    const invalid = list.find((file) => !file.name.toLowerCase().endsWith(".xlsx"));
    if (invalid) {
      setUploadMsgType("error");
      setUploadMsg(`Только .xlsx файлы поддерживаются (${invalid.name})`);
      return;
    }
    setUploading(true);
    setUploadMsg("");
    let uploaded = 0;
    try {
      for (const file of list) {
        const key = `${file.name}-${file.size}-${file.lastModified}-${Date.now()}`;
        const activeUpload: ActiveUpload = {
          key,
          filename: file.name,
          size: file.size,
          status: "sending",
          message: "Отправка файла на сервер...",
        };
        setActiveUploads((prev) => [
          activeUpload,
          ...prev,
        ].slice(0, 12));

        try {
          const upload = await uploads.uploadExcel(file);
          setActiveUploads((prev) =>
            prev.map((item) =>
              item.key === key
                ? {
                    ...item,
                    uploadId: upload.id,
                    status: "accepted",
                    message: "Файл принят, обработка началась",
                  }
                : item
            )
          );
        } catch (err) {
          const message = err instanceof Error ? err.message : "Ошибка загрузки";
          setActiveUploads((prev) =>
            prev.map((item) =>
              item.key === key
                ? { ...item, status: "failed", message }
                : item
            )
          );
          throw err;
        }
        uploaded += 1;
      }
      setUploadMsgType("success");
      setUploadMsg(`✓ Принято файлов: ${uploaded}. Обработка начата...`);
      await fetchUploads();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Ошибка загрузки";
      setUploadMsgType("error");
      setUploadMsg(`✗ ${message}. Загружено до ошибки: ${uploaded}`);
    } finally {
      setUploading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files?.length) handleFiles(files);
    e.target.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const files = e.dataTransfer.files;
    if (files?.length) handleFiles(files);
  };

  const runScoring = async (uploadId: string) => {
    try {
      const res = await scoring.run(parseInt(uploadId));
      setScoringJobs((prev) => ({ ...prev, [uploadId]: { ...res, upload_id: parseInt(uploadId), finished_at: null, error_message: null } as ScoringStatusResponse }));
      // Start polling
      const interval = setInterval(async () => {
        try {
          const status = await scoring.status(res.job_id);
          setScoringJobs((prev) => ({ ...prev, [uploadId]: status }));
          if (status.status === "done" || status.status === "failed") {
            clearInterval(interval);
            fetchUploads();
          }
        } catch {
          clearInterval(interval);
        }
      }, 3000);
    } catch (e) {
      console.error("Scoring run error:", e);
    }
  };

  const statusIcon = (status: string) => {
    switch (normalizeUploadStatus(status)) {
      case "sending": return <Loader2 size={16} style={{ color: "#3b82f6", animation: "spin 1s linear infinite" }} />;
      case "accepted": return <Clock size={16} style={{ color: "#f59e0b" }} />;
      case "done": return <CheckCircle2 size={16} style={{ color: "#10b981" }} />;
      case "pending": return <Clock size={16} style={{ color: "#f59e0b" }} />;
      case "processing": case "running": return <Loader2 size={16} style={{ color: "#3b82f6", animation: "spin 1s linear infinite" }} />;
      case "failed": return <AlertTriangle size={16} style={{ color: "#ef4444" }} />;
      default: return <Clock size={16} style={{ color: "var(--text-muted)" }} />;
    }
  };

  const completedUploads = uploadList.filter(u => normalizeUploadStatus(u.status) === "done").length;
  const scoredUploads = Object.keys(scoringJobs).filter(k => scoringJobs[k].status === "done").length;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Загрузка и скоринг</h1>
          <p className="page-subtitle">Импорт данных и анализ рисков</p>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 24 }}>
        {[
          { label: "Всего загрузок", count: uploadList.length, icon: "📁" },
          { label: "Завершено", count: completedUploads, icon: "✓" },
          { label: "Обработано", count: scoredUploads, icon: "⚡" },
        ].map((stat, i) => (
          <motion.div
            key={i}
            className="card"
            style={{ padding: 16 }}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginBottom: 8 }}>{stat.label}</p>
            <p className="mono" style={{ fontWeight: 800, fontSize: "1.75rem" }}>{stat.count}</p>
          </motion.div>
        ))}
      </div>

      {/* Upload Zone */}
      <motion.div className="card" style={{ padding: 48, textAlign: "center", marginBottom: 24 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ width: 72, height: 72, borderRadius: "var(--radius-xl)", background: "var(--risk-low-bg)", color: "var(--risk-low)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 24px" }}>
          <FileSpreadsheet size={32} />
        </div>
        <h2 style={{ marginBottom: 8 }}>Загрузка файлов</h2>
        <p style={{ color: "var(--text-secondary)", marginBottom: 24 }}>Выберите Excel-файл с данными о продажах или возвратах для анализа.</p>

        <div
          className={`upload-zone ${dragging ? "dragging" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => document.getElementById("fileInput")?.click()}
        >
          <input type="file" id="fileInput" accept=".xlsx" multiple style={{ display: "none" }} onChange={handleInputChange} />
          <UploadIcon size={40} style={{ color: dragging ? "var(--accent)" : "var(--text-muted)", marginBottom: 16, transition: "color 0.2s" }} />
          <p style={{ fontWeight: 600, color: "var(--text-secondary)" }}>
            {uploading ? "Загрузка..." : "Нажмите или перетащите один/несколько файлов"}
          </p>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginTop: 8 }}>XLSX до 500MB</p>
        </div>

        {uploadMsg && (
          <motion.div
            style={{
              marginTop: 20,
              padding: 12,
              borderRadius: "var(--radius-md)",
              background: uploadMsgType === "success" ? "var(--risk-low-bg)" : "var(--risk-critical-bg)",
              fontSize: "0.875rem",
              fontWeight: 500,
              color: uploadMsgType === "success" ? "#10b981" : "#ef4444",
              border: `1px solid ${uploadMsgType === "success" ? "#d1fae5" : "#fee2e2"}`,
            }}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {uploadMsg}
          </motion.div>
        )}

        {activeUploads.length > 0 && (
          <div style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 8, textAlign: "left" }}>
            {activeUploads.map((item) => (
              <div
                key={item.key}
                style={{
                  display: "grid",
                  gridTemplateColumns: "auto 1fr auto",
                  gap: 12,
                  alignItems: "center",
                  padding: "12px 14px",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius-md)",
                  background: "var(--surface-elevated)",
                }}
              >
                {statusIcon(item.status)}
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 650, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {item.filename}
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.8125rem", marginTop: 2 }}>
                    {item.message}
                  </div>
                </div>
                <div className="mono" style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>
                  {formatFileSize(item.size)}
                </div>
              </div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Upload History */}
      <motion.div className="card" style={{ padding: 24 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <h3 style={{ fontSize: "1rem", marginBottom: 20, display: "flex", alignItems: "center", gap: 8 }}>
          <TrendingUp size={18} /> История загрузок
        </h3>
        {loading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {[...Array(3)].map((_, i) => <div key={i} className="skeleton" style={{ height: 60 }} />)}
          </div>
        ) : uploadList.length === 0 ? (
          <div className="empty-state"><p>Нет загрузок</p></div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Файл</th>
                  <th>Статус загрузки</th>
                  <th>Дата</th>
                  <th>Скоринг</th>
                  <th style={{ textAlign: "right" }}>Действия</th>
                </tr>
              </thead>
              <tbody>
                {uploadList.map((u) => {
                  const job = scoringJobs[u.id];
                  const uploadStatus = normalizeUploadStatus(u.status);
                  const isScoringReady = uploadStatus === "done";
                  const isScoring = !!job;

                  return (
                    <motion.tr
                      key={u.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.2 }}
                    >
                      <td className="mono" style={{ color: "var(--text-muted)", fontWeight: 600 }}>#{u.id}</td>
                      <td style={{ fontWeight: 500 }}>{u.filename}</td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          {statusIcon(u.status)}
                          <span style={{ fontSize: "0.8125rem", textTransform: "uppercase", fontWeight: 600 }}>
                            {uploadStatus === "done" ? "Готово" : uploadStatus === "processing" ? "Обработка" : uploadStatus === "pending" ? "В очереди" : uploadStatus || u.status}
                          </span>
                        </div>
                      </td>
                      <td style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                        {new Date(u.uploaded_at).toLocaleString("ru-RU", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                      </td>
                      <td>
                        {isScoring ? (
                          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.8125rem" }}>
                            {statusIcon(job.status)}
                            <span style={{ textTransform: "uppercase", fontWeight: 600 }}>
                              {job.status === "done" ? "Завершено" : job.status === "running" ? "Обработка" : job.status}
                            </span>
                          </div>
                        ) : (
                          <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>—</span>
                        )}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        {!isScoring && isScoringReady && (
                          <motion.button
                            className="btn btn-primary btn-sm"
                            onClick={() => runScoring(u.id)}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                          >
                            <Zap size={14} /> Скорить
                          </motion.button>
                        )}
                        {isScoring && job.status !== "done" && job.status !== "failed" && (
                          <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: "0.75rem", color: "var(--text-muted)" }}>
                            <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} /> Обработка...
                          </div>
                        )}
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>
    </div>
  );
}
