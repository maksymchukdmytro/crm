import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { errText, useMeta, useToast } from "../lib/app";
import { Field } from "../components/ui";

export function LoginPage() {
  const qc = useQueryClient();
  const [f, setF] = useState({ username: "", password: "" });
  const [err, setErr] = useState("");
  const login = useMutation({
    mutationFn: () => api.post("/auth/login", f),
    onSuccess: () => { setErr(""); qc.invalidateQueries({ queryKey: ["meta"] }); },
    onError: (e) => setErr(errText(e)),
  });
  return (
    <div className="login-wrap">
      <form className="login card" onSubmit={(e) => { e.preventDefault(); login.mutate(); }}>
        <div className="brand dark"><span className="brand-mark" /><span>CRM</span></div>
        <h1>Вхід до системи</h1>
        {err && <div className="flash error">{err}</div>}
        <Field label="Логін"><input value={f.username} onChange={(e) => setF({ ...f, username: e.target.value })} autoComplete="username" autoFocus required /></Field>
        <Field label="Пароль"><input type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} autoComplete="current-password" required /></Field>
        <button className="btn primary wide" disabled={login.isPending}>{login.isPending ? "Вхід…" : "Увійти"}</button>
      </form>
    </div>
  );
}

export function ProfilePage() {
  const meta = useMeta();
  const qc = useQueryClient();
  const toast = useToast();
  const [f, setF] = useState({ full_name: meta.user.full_name, old_password: "", new_password: "" });
  const save = useMutation({
    mutationFn: () => api.patch("/me", f),
    onSuccess: () => { toast("Збережено"); setF({ ...f, old_password: "", new_password: "" }); qc.invalidateQueries({ queryKey: ["meta"] }); },
    onError: (e) => toast(errText(e), "error"),
  });
  return (
    <div>
      <div className="head"><h1>Мій профіль</h1></div>
      <form className="card form narrow" onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
        <Field label="Логін"><input value={meta.user.username} disabled /></Field>
        <Field label="Ім'я"><input value={f.full_name} onChange={(e) => setF({ ...f, full_name: e.target.value })} /></Field>
        <h3>Зміна пароля</h3>
        <Field label="Поточний пароль"><input type="password" value={f.old_password} onChange={(e) => setF({ ...f, old_password: e.target.value })} autoComplete="current-password" /></Field>
        <Field label="Новий пароль" hint="Щонайменше 8 символів"><input type="password" minLength={8} value={f.new_password} onChange={(e) => setF({ ...f, new_password: e.target.value })} autoComplete="new-password" /></Field>
        <button className="btn primary mt" disabled={save.isPending}>Зберегти</button>
      </form>
    </div>
  );
}
