import { useEffect, useState } from "react";
import { apiRequest } from "../api.js";

const initialForm = {
  username: "",
  email: "",
  password: "",
  role: "client",
};

export default function AdminPanel({ token }) {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadUsers = async () => {
    try {
      setUsers(await apiRequest("/users/", { token }));
      setError("");
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadUsers();
  }, [token]);

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const createUser = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await apiRequest("/users/", { method: "POST", token, body: form });
      setForm(initialForm);
      setMessage("Пользователь добавлен");
      await loadUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteUser = async (userId) => {
    setError("");
    setMessage("");
    try {
      await apiRequest(`/users/${userId}`, { method: "DELETE", token });
      setMessage("Пользователь удалён");
      await loadUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <section className="admin-layout">
      <form className="panel form-panel" onSubmit={createUser}>
        <div>
          <p className="eyebrow">Администрирование</p>
          <h2>Добавить пользователя</h2>
        </div>
        <label>
          Ник
          <input value={form.username} onChange={(event) => updateField("username", event.target.value)} required />
        </label>
        <label>
          Email
          <input type="email" value={form.email} onChange={(event) => updateField("email", event.target.value)} required />
        </label>
        <label>
          Пароль
          <input type="password" value={form.password} onChange={(event) => updateField("password", event.target.value)} minLength="6" required />
        </label>
        <label>
          Роль
          <select value={form.role} onChange={(event) => updateField("role", event.target.value)}>
            <option value="client">Клиент</option>
            <option value="psychologist">Психолог</option>
            <option value="admin">Администратор</option>
          </select>
        </label>
        <button className="primary-button">Добавить</button>
      </form>

      <div className="panel users-panel">
        <div>
          <p className="eyebrow">Пользователи</p>
          <h2>Все аккаунты</h2>
        </div>
        {error && <div className="error">{error}</div>}
        {message && <div className="success">{message}</div>}
        <div className="user-table">
          {users.map((item) => (
            <div className="user-row" key={item.id}>
              <div>
                <strong>@{item.username}</strong>
                <span>{item.email}</span>
              </div>
              <span className="role-pill">{item.role}</span>
              <button className="danger-button" onClick={() => deleteUser(item.id)}>
                Удалить
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
