import { useState } from "react";
import { apiRequest } from "../api.js";

export default function Profile({ user, token, onUserChange }) {
  const [form, setForm] = useState({
    full_name: user.full_name || "",
    specialization: user.specialization || "",
    education: user.education || "",
    about: user.about || "",
  });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const body =
        user.role === "psychologist"
          ? {
              full_name: form.full_name,
              specialization: form.specialization,
              education: form.education,
            }
          : {
              specialization: form.specialization,
              about: form.about,
            };
      const updated = await apiRequest("/users/me", { method: "PUT", token, body });
      onUserChange(updated);
      setMessage("Профиль обновлён");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <section className="profile-layout">
      <aside className="panel profile-card">
        <h2>@{user.username}</h2>
        <p>{user.role === "psychologist" ? "Психолог" : user.role === "client" ? "Клиент" : "Администратор"}</p>
        {user.role === "psychologist" && (
          <div className="rating">
            <strong>{Number(user.rating || 0).toFixed(1)}</strong>
            <span>рейтинг на основе {user.rating_count || 0} отзывов</span>
          </div>
        )}
      </aside>

      <form className="panel form-panel" onSubmit={submit}>
        <div>
          <p className="eyebrow">Профиль</p>
          <h2>Данные пользователя</h2>
        </div>

        {user.role === "psychologist" && (
          <>
            <label>
              Настоящее ФИО
              <input value={form.full_name} onChange={(event) => updateField("full_name", event.target.value)} />
            </label>
            <label>
              Специализация
              <input value={form.specialization} onChange={(event) => updateField("specialization", event.target.value)} />
            </label>
            <label>
              Образование
              <textarea value={form.education} onChange={(event) => updateField("education", event.target.value)} rows="5" />
            </label>
          </>
        )}

        {user.role === "client" && (
          <>
            <label>
              Специализация запроса
              <input value={form.specialization} onChange={(event) => updateField("specialization", event.target.value)} />
            </label>
            <label>
              Информация о себе
              <textarea value={form.about} onChange={(event) => updateField("about", event.target.value)} rows="5" />
            </label>
          </>
        )}

        {user.role === "admin" && <div className="empty">Профиль администратора используется для управления пользователями.</div>}

        {error && <div className="error">{error}</div>}
        {message && <div className="success">{message}</div>}
        {user.role !== "admin" && <button className="primary-button">Сохранить</button>}
      </form>
    </section>
  );
}
