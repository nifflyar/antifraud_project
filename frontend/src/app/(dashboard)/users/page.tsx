"use client";

import React, { useEffect, useState, useCallback } from "react";
import { users, auth } from "@/lib/api";
import type { UserListItem, RegisterRequest } from "@/types/api";
import { useAuth } from "@/lib/auth-context";
import { UserCog, Plus, Trash2, Edit, X, Shield, User } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const [userList, setUserList] = useState<UserListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editAdmin, setEditAdmin] = useState(false);
  const [form, setForm] = useState<RegisterRequest>({ email: "", password: "", full_name: "", is_admin: false });
  const [error, setError] = useState("");

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await users.list(100, 0);
      setUserList(res.users);
    } catch (e) {
      console.error("Users fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await auth.register(form);
      setShowCreate(false);
      setForm({ email: "", password: "", full_name: "", is_admin: false });
      fetchUsers();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ошибка создания");
    }
  };

  const handleUpdate = async (id: number) => {
    try {
      await users.update(id, { full_name: editName, is_admin: editAdmin });
      setEditingId(null);
      fetchUsers();
    } catch (e) {
      console.error("Update error:", e);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Удалить пользователя?")) return;
    try {
      await users.delete(id);
      fetchUsers();
    } catch (e) {
      console.error("Delete error:", e);
    }
  };

  if (!currentUser?.is_admin) {
    return (
      <div className="empty-state" style={{ minHeight: "60vh" }}>
        <div className="empty-state-icon"><Shield size={28} /></div>
        <p>Эта страница доступна только администраторам</p>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Управление пользователями</h1>
          <p className="page-subtitle">Создание, редактирование и удаление учётных записей</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={16} /> Новый пользователь
        </button>
      </div>

      {/* Create Modal */}
      <AnimatePresence>
        {showCreate && (
          <motion.div className="modal-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setShowCreate(false)}>
            <motion.div className="modal-content" initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }} onClick={(e) => e.stopPropagation()}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <h3 className="modal-title" style={{ marginBottom: 0 }}>Новый пользователь</h3>
                <button className="btn btn-ghost btn-icon" onClick={() => setShowCreate(false)}><X size={18} /></button>
              </div>
              <form onSubmit={handleCreate}>
                <div className="form-group">
                  <label className="form-label">Полное имя</label>
                  <input className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Email</label>
                  <input className="input" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Пароль</label>
                  <input className="input" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontSize: "0.875rem" }}>
                    <input type="checkbox" checked={form.is_admin} onChange={(e) => setForm({ ...form, is_admin: e.target.checked })} />
                    Администратор
                  </label>
                </div>
                {error && <div className="form-error" style={{ marginBottom: 16 }}>{error}</div>}
                <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                  <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>Отмена</button>
                  <button type="submit" className="btn btn-primary">Создать</button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Users Table */}
      <motion.div className="card" style={{ padding: 24 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Имя</th>
              <th>Email</th>
              <th>Роль</th>
              <th>Статус</th>
              <th>Создан</th>
              <th>Последний вход</th>
              <th style={{ textAlign: "right" }}>Действия</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [...Array(3)].map((_, i) => (
                <tr key={i}>{[...Array(8)].map((__, j) => <td key={j}><div className="skeleton" style={{ width: 80, height: 16 }} /></td>)}</tr>
              ))
            ) : userList.length === 0 ? (
              <tr><td colSpan={8}><div className="empty-state"><p>Нет пользователей</p></div></td></tr>
            ) : (
              userList.map((u) => (
                <tr key={u.id}>
                  <td className="mono" style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>#{u.id}</td>
                  <td>
                    {editingId === parseInt(u.id) ? (
                      <input className="input" value={editName} onChange={(e) => setEditName(e.target.value)} style={{ width: 160, padding: "4px 8px", fontSize: "0.8125rem" }} />
                    ) : (
                      <span style={{ fontWeight: 600 }}>{u.full_name}</span>
                    )}
                  </td>
                  <td style={{ color: "var(--text-secondary)", fontSize: "0.8125rem" }}>{u.email}</td>
                  <td>
                    {editingId === parseInt(u.id) ? (
                      <label style={{ display: "flex", alignItems: "center", gap: 4, fontSize: "0.8125rem" }}>
                        <input type="checkbox" checked={editAdmin} onChange={(e) => setEditAdmin(e.target.checked)} /> Admin
                      </label>
                    ) : (
                      <span className="badge" style={{ background: u.is_admin ? "var(--accent-light)" : "var(--bg-secondary)", color: u.is_admin ? "var(--accent)" : "var(--text-secondary)" }}>
                        {u.is_admin ? <Shield size={10} /> : <User size={10} />}
                        {u.is_admin ? "Admin" : "Analyst"}
                      </span>
                    )}
                  </td>
                  <td>
                    <span className="badge" style={{ background: u.is_active ? "var(--risk-low-bg)" : "var(--bg-secondary)", color: u.is_active ? "var(--risk-low)" : "var(--text-muted)" }}>
                      {u.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", whiteSpace: "nowrap" }}>
                    {u.created_at ? new Date(u.created_at).toLocaleDateString("ru-RU") : "—"}
                  </td>
                  <td style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", whiteSpace: "nowrap" }}>
                    {u.last_login_at ? new Date(u.last_login_at).toLocaleString("ru-RU") : "—"}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <div style={{ display: "flex", gap: 4, justifyContent: "flex-end" }}>
                      {editingId === parseInt(u.id) ? (
                        <>
                          <button className="btn btn-primary btn-sm" onClick={() => handleUpdate(parseInt(u.id))}>Сохранить</button>
                          <button className="btn btn-ghost btn-sm" onClick={() => setEditingId(null)}>Отмена</button>
                        </>
                      ) : (
                        <>
                          <button className="btn btn-ghost btn-icon" onClick={() => { setEditingId(parseInt(u.id)); setEditName(u.full_name); setEditAdmin(u.is_admin); }}>
                            <Edit size={14} />
                          </button>
                          <button className="btn btn-ghost btn-icon" style={{ color: "var(--error)" }} onClick={() => handleDelete(parseInt(u.id))}>
                            <Trash2 size={14} />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </motion.div>
    </div>
  );
}
