"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { auth, users } from "@/lib/api";
import type { RegisterRequest, UserListItem } from "@/types/api";
import { useAuth } from "@/lib/auth-context";
import {
  AlertCircle,
  CheckCircle2,
  Edit,
  Plus,
  RefreshCw,
  Save,
  Search,
  Shield,
  Trash2,
  User,
  UserCog,
  X,
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

type UserRole = "analyst" | "security" | "admin";

type EditForm = {
  full_name: string;
  role: UserRole;
  is_active: boolean;
};

const roleLabels: Record<UserRole, string> = {
  analyst: "Аналитик",
  security: "Служба безопасности",
  admin: "Администратор",
};

const emptyCreateForm: RegisterRequest = {
  email: "",
  password: "",
  full_name: "",
  role: "analyst",
  is_admin: false,
};

function roleFromUser(user: UserListItem): UserRole {
  if (user.is_admin) return "admin";
  if (user.role === "security") return "security";
  return "analyst";
}

function roleBadgeStyle(role: UserRole) {
  if (role === "admin") {
    return { background: "var(--accent-light)", color: "var(--accent)" };
  }
  if (role === "security") {
    return { background: "var(--risk-medium-bg)", color: "var(--risk-medium)" };
  }
  return { background: "var(--bg-secondary)", color: "var(--text-secondary)" };
}

export default function UsersPage() {
  const { user: currentUser, refresh } = useAuth();
  const [userList, setUserList] = useState<UserListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<RegisterRequest>(emptyCreateForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<EditForm>({ full_name: "", role: "analyst", is_active: true });
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [savingCreate, setSavingCreate] = useState(false);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await users.list(100, 0);
      setUserList(res.users || []);
      setTotal(res.total || res.users?.length || 0);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить пользователей");
      setUserList([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  useEffect(() => {
    if (!success) return;
    const timer = window.setTimeout(() => setSuccess(""), 3500);
    return () => window.clearTimeout(timer);
  }, [success]);

  const stats = useMemo(() => {
    const active = userList.filter((u) => u.is_active).length;
    const admins = userList.filter((u) => u.is_admin).length;
    const inactive = userList.length - active;
    return { active, admins, inactive };
  }, [userList]);

  const filteredUsers = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return userList;
    return userList.filter((u) =>
      u.full_name.toLowerCase().includes(q)
      || u.email.toLowerCase().includes(q)
      || u.id.includes(q)
      || roleLabels[roleFromUser(u)].toLowerCase().includes(q)
    );
  }, [query, userList]);

  const startEdit = (user: UserListItem) => {
    setError("");
    setSuccess("");
    setEditingId(user.id);
    setEditForm({
      full_name: user.full_name,
      role: roleFromUser(user),
      is_active: user.is_active,
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({ full_name: "", role: "analyst", is_active: true });
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSavingCreate(true);
    try {
      const role = (form.role as UserRole) || "analyst";
      await auth.register({
        ...form,
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        role,
        is_admin: role === "admin",
      });
      setShowCreate(false);
      setForm(emptyCreateForm);
      setSuccess("Пользователь создан");
      await fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка создания пользователя");
    } finally {
      setSavingCreate(false);
    }
  };

  const handleUpdate = async (user: UserListItem) => {
    setError("");
    setSuccess("");
    const fullName = editForm.full_name.trim();
    if (!fullName) {
      setError("Имя пользователя не может быть пустым");
      return;
    }

    setSavingId(user.id);
    try {
      await users.update(user.id, {
        full_name: fullName,
        role: editForm.role,
        is_admin: editForm.role === "admin",
        is_active: editForm.is_active,
      });
      setUserList((prev) =>
        prev.map((item) =>
          item.id === user.id
            ? {
                ...item,
                full_name: fullName,
                role: editForm.role,
                is_admin: editForm.role === "admin",
                is_active: editForm.is_active,
              }
            : item
        )
      );
      setEditingId(null);
      setSuccess("Изменения сохранены");
      if (currentUser?.id === user.id) await refresh();
      await fetchUsers();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить пользователя");
    } finally {
      setSavingId(null);
    }
  };

  const handleDelete = async (user: UserListItem) => {
    setError("");
    setSuccess("");
    if (currentUser?.id === user.id) {
      setError("Нельзя удалить свою текущую учётную запись");
      return;
    }
    if (!window.confirm(`Удалить пользователя ${user.full_name}?`)) return;

    setDeletingId(user.id);
    try {
      await users.delete(user.id);
      setUserList((prev) => prev.filter((item) => item.id !== user.id));
      setTotal((value) => Math.max(0, value - 1));
      setSuccess("Пользователь удалён");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось удалить пользователя");
    } finally {
      setDeletingId(null);
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
          <p className="page-subtitle">Создание, роли, доступ и состояние учётных записей</p>
        </div>
        <button className="btn btn-primary" onClick={() => { setError(""); setShowCreate(true); }}>
          <Plus size={16} /> Новый пользователь
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Всего", value: total, color: "var(--text-primary)", icon: <UserCog size={16} /> },
          { label: "Активные", value: stats.active, color: "var(--risk-low)", icon: <CheckCircle2 size={16} /> },
          { label: "Администраторы", value: stats.admins, color: "var(--accent)", icon: <Shield size={16} /> },
          { label: "Отключены", value: stats.inactive, color: "var(--text-muted)", icon: <X size={16} /> },
        ].map((item) => (
          <div key={item.label} className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, color: item.color, marginBottom: 8 }}>
              {item.icon}
              <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>{item.label}</span>
            </div>
            <p className="mono" style={{ fontWeight: 800, fontSize: "1.5rem", color: item.color }}>{item.value}</p>
          </div>
        ))}
      </div>

      {(error || success) && (
        <div
          className="card"
          style={{
            padding: 12,
            marginBottom: 16,
            borderColor: error ? "var(--error)" : "var(--risk-low)",
            color: error ? "var(--error)" : "var(--risk-low)",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          {error ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
          <span style={{ fontSize: "0.875rem", fontWeight: 700 }}>{error || success}</span>
        </div>
      )}

      <AnimatePresence>
        {showCreate && (
          <motion.div className="modal-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => !savingCreate && setShowCreate(false)}>
            <motion.div className="modal-content" initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }} onClick={(e) => e.stopPropagation()}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <h3 className="modal-title" style={{ marginBottom: 0 }}>Новый пользователь</h3>
                <button className="btn btn-ghost btn-icon" disabled={savingCreate} onClick={() => setShowCreate(false)}><X size={18} /></button>
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
                  <input className="input" type="password" minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Роль</label>
                  <select
                    className="select"
                    value={(form.role as UserRole) || "analyst"}
                    onChange={(e) => {
                      const role = e.target.value as UserRole;
                      setForm({ ...form, role, is_admin: role === "admin" });
                    }}
                  >
                    <option value="analyst">Аналитик</option>
                    <option value="security">Служба безопасности</option>
                    <option value="admin">Администратор</option>
                  </select>
                </div>
                <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 20 }}>
                  <button type="button" className="btn btn-secondary" disabled={savingCreate} onClick={() => setShowCreate(false)}>Отмена</button>
                  <button type="submit" className="btn btn-primary" disabled={savingCreate}>
                    {savingCreate ? <RefreshCw size={14} /> : <Plus size={14} />}
                    {savingCreate ? "Создание..." : "Создать"}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div className="card" style={{ padding: 24 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, marginBottom: 18, flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <UserCog size={20} style={{ color: "var(--accent)" }} />
            <h2 style={{ fontSize: "1.125rem", fontWeight: 800 }}>Пользователи</h2>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <div style={{ position: "relative" }}>
              <Search size={15} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
              <input
                className="input"
                placeholder="Поиск по имени, email, роли"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                style={{ paddingLeft: 36, width: 260 }}
              />
            </div>
            <button className="btn btn-secondary btn-sm" onClick={fetchUsers} disabled={loading}>
              <RefreshCw size={14} /> Обновить
            </button>
          </div>
        </div>

        <div style={{ overflowX: "auto" }}>
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
                [...Array(5)].map((_, i) => (
                  <tr key={i}>{[...Array(8)].map((__, j) => <td key={j}><div className="skeleton" style={{ width: j === 1 ? 140 : 80, height: 16 }} /></td>)}</tr>
                ))
              ) : filteredUsers.length === 0 ? (
                <tr><td colSpan={8}><div className="empty-state"><p>Пользователи не найдены</p></div></td></tr>
              ) : (
                filteredUsers.map((u) => {
                  const isEditing = editingId === u.id;
                  const role = roleFromUser(u);
                  const isSelf = currentUser?.id === u.id;
                  const isBusy = savingId === u.id || deletingId === u.id;
                  return (
                    <tr key={u.id}>
                      <td className="mono" style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>#{u.id}</td>
                      <td>
                        {isEditing ? (
                          <input
                            className="input"
                            value={editForm.full_name}
                            onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                            style={{ minWidth: 180, padding: "6px 8px", fontSize: "0.8125rem" }}
                          />
                        ) : (
                          <span style={{ fontWeight: 700 }}>{u.full_name}</span>
                        )}
                      </td>
                      <td style={{ color: "var(--text-secondary)", fontSize: "0.8125rem" }}>{u.email}</td>
                      <td>
                        {isEditing ? (
                          <select
                            className="select"
                            value={editForm.role}
                            onChange={(e) => setEditForm({ ...editForm, role: e.target.value as UserRole })}
                            disabled={isSelf}
                            style={{ minWidth: 160, padding: "6px 8px", fontSize: "0.8125rem" }}
                          >
                            <option value="analyst">Аналитик</option>
                            <option value="security">Безопасность</option>
                            <option value="admin">Администратор</option>
                          </select>
                        ) : (
                          <span className="badge" style={roleBadgeStyle(role)}>
                            {role === "admin" ? <Shield size={10} /> : <User size={10} />}
                            {roleLabels[role]}
                          </span>
                        )}
                      </td>
                      <td>
                        {isEditing ? (
                          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.8125rem", color: isSelf ? "var(--text-muted)" : "var(--text-secondary)" }}>
                            <input
                              type="checkbox"
                              checked={editForm.is_active}
                              disabled={isSelf}
                              onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                            />
                            Активен
                          </label>
                        ) : (
                          <span className="badge" style={{ background: u.is_active ? "var(--risk-low-bg)" : "var(--bg-secondary)", color: u.is_active ? "var(--risk-low)" : "var(--text-muted)" }}>
                            {u.is_active ? "Активен" : "Отключён"}
                          </span>
                        )}
                      </td>
                      <td style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", whiteSpace: "nowrap" }}>
                        {u.created_at ? new Date(u.created_at).toLocaleDateString("ru-RU") : "—"}
                      </td>
                      <td style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", whiteSpace: "nowrap" }}>
                        {u.last_login_at ? new Date(u.last_login_at).toLocaleString("ru-RU") : "—"}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                          {isEditing ? (
                            <>
                              <button className="btn btn-primary btn-sm" disabled={isBusy} onClick={() => handleUpdate(u)}>
                                <Save size={14} /> {savingId === u.id ? "Сохранение..." : "Сохранить"}
                              </button>
                              <button className="btn btn-ghost btn-sm" disabled={isBusy} onClick={cancelEdit}>Отмена</button>
                            </>
                          ) : (
                            <>
                              <button className="btn btn-ghost btn-icon" disabled={Boolean(editingId) || isBusy} onClick={() => startEdit(u)} title="Редактировать">
                                <Edit size={14} />
                              </button>
                              <button
                                className="btn btn-ghost btn-icon"
                                style={{ color: isSelf ? "var(--text-muted)" : "var(--error)" }}
                                disabled={isSelf || Boolean(editingId) || isBusy}
                                onClick={() => handleDelete(u)}
                                title={isSelf ? "Нельзя удалить текущего пользователя" : "Удалить"}
                              >
                                <Trash2 size={14} />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}
