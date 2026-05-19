import { useState } from "react";
import { apiRequest } from "../api.js";

const initialForm = {
  username: "",
  email: "",
  password: "",
  role: "client",
};

export default function AuthModal({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const path = mode === "login" ? "/auth/login" : "/auth/register";
      const body =
        mode === "login"
          ? { username: form.username, password: form.password }
          : {
              username: form.username,
              email: form.email,
              password: form.password,
              role: form.role,
            };
      const data = await apiRequest(path, { method: "POST", body });
      onAuth(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <form className="auth-modal" onSubmit={submit}>
        <div>
          <p className="eyebrow">Платформа психологических консультаций</p>
          <h1>{mode === "login" ? "Вход" : "Регистрация"}</h1>
        </div>

        <div className="segmented">
          <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
            Войти
          </button>
          <button type="button" className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>
            Зарегистрироваться
          </button>
        </div>

        <label>
          Ник или email
          <input value={form.username} onChange={(event) => updateField("username", event.target.value)} required />
        </label>

        {mode === "register" && (
          <>
            <label>
              Email
              <input type="email" value={form.email} onChange={(event) => updateField("email", event.target.value)} required />
            </label>
            <label>
              Роль
              <select value={form.role} onChange={(event) => updateField("role", event.target.value)}>
                <option value="client">Клиент</option>
                <option value="psychologist">Психолог</option>
              </select>
            </label>
          </>
        )}

        <label>
          Пароль
          <input
            type="password"
            value={form.password}
            onChange={(event) => updateField("password", event.target.value)}
            minLength={6}
            required
          />
        </label>

        {error && <div className="error">{error}</div>}

        <button className="primary-button" disabled={loading}>
          {loading ? "Проверяем..." : mode === "login" ? "Войти" : "Создать аккаунт"}
        </button>

      </form>
    </div>
  );
}
