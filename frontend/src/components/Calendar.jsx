import { useEffect, useMemo, useState } from "react";
import { apiRequest } from "../api.js";

const emptySlot = {
  start_at: "",
  end_at: "",
  specialization: "",
  meeting_link: "",
};

function formatDate(value) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function Calendar({ user, token }) {
  const [slots, setSlots] = useState([]);
  const [form, setForm] = useState(emptySlot);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const loadSlots = async () => {
    setLoading(true);
    try {
      setSlots(await apiRequest("/slots/", { token }));
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSlots();
  }, [token]);

  const groupedSlots = useMemo(() => {
    return slots.reduce((groups, slot) => {
      const day = new Intl.DateTimeFormat("ru-RU", {
        weekday: "long",
        day: "2-digit",
        month: "long",
      }).format(new Date(slot.start_at));
      groups[day] = groups[day] || [];
      groups[day].push(slot);
      return groups;
    }, {});
  }, [slots]);

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const createSlot = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await apiRequest("/slots/", { method: "POST", token, body: form });
      setForm(emptySlot);
      setMessage("Слот добавлен");
      await loadSlots();
    } catch (err) {
      setError(err.message);
    }
  };

  const bookSlot = async (slotId) => {
    setError("");
    setMessage("");
    try {
      await apiRequest(`/slots/${slotId}/book`, { method: "POST", token });
      setMessage("Вы записались на консультацию");
      await loadSlots();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteSlot = async (slotId) => {
    setError("");
    setMessage("");
    try {
      await apiRequest(`/slots/${slotId}`, { method: "DELETE", token });
      setMessage("Слот удалён");
      await loadSlots();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <section className="content-grid calendar-layout">
      {user.role === "psychologist" && (
        <form className="panel form-panel" onSubmit={createSlot}>
          <div>
            <p className="eyebrow">Рабочее расписание</p>
            <h2>Новый слот</h2>
          </div>
          <label>
            С
            <input type="datetime-local" value={form.start_at} onChange={(event) => updateField("start_at", event.target.value)} required />
          </label>
          <label>
            До
            <input type="datetime-local" value={form.end_at} onChange={(event) => updateField("end_at", event.target.value)} required />
          </label>
          <label>
            Специализация консультации
            <input value={form.specialization} onChange={(event) => updateField("specialization", event.target.value)} required />
          </label>
          <label>
            Ссылка на видеоконсультацию
            <input value={form.meeting_link} onChange={(event) => updateField("meeting_link", event.target.value)} required />
          </label>
          <button className="primary-button">Добавить слот</button>
        </form>
      )}

      <div className="panel slots-panel">
        <div className="section-title">
          <div>
            <p className="eyebrow">Календарь консультаций</p>
            <h2>Доступные и занятые слоты</h2>
          </div>
          <div className="legend">
            <span><i className="free-dot" /> Свободен</span>
            <span><i className="busy-dot" /> Занят</span>
          </div>
        </div>

        {error && <div className="error">{error}</div>}
        {message && <div className="success">{message}</div>}
        {loading && <div className="empty">Загружаем календарь...</div>}

        {!loading && Object.keys(groupedSlots).length === 0 && <div className="empty">Пока нет слотов</div>}

        <div className="day-groups">
          {Object.entries(groupedSlots).map(([day, daySlots]) => (
            <div className="day-group" key={day}>
              <h3>{day}</h3>
              <div className="slot-list">
                {daySlots.map((slot) => {
                  const ownSlot = slot.psychologist_id === user.id;
                  const bookedByMe = slot.client_id === user.id;
                  return (
                    <article key={slot.id} className={`slot-card ${slot.is_booked ? "busy" : "free"}`}>
                      <div>
                        <strong>{formatDate(slot.start_at)} - {formatDate(slot.end_at).split(", ").pop()}</strong>
                        <p>{slot.specialization}</p>
                      </div>
                      <div className="slot-meta">
                        <span>Психолог: @{slot.psychologist_username}</span>
                        {slot.psychologist_full_name && <span>{slot.psychologist_full_name}</span>}
                        {slot.client_username && <span>Клиент: @{slot.client_username}</span>}
                      </div>
                      {slot.meeting_link && (
                        <a className="meeting-link" href={slot.meeting_link} target="_blank" rel="noreferrer">
                          Ссылка на консультацию
                        </a>
                      )}
                      {user.role === "client" && !slot.is_booked && (
                        <button className="primary-button" onClick={() => bookSlot(slot.id)}>
                          Записаться
                        </button>
                      )}
                      {(user.role === "admin" || (user.role === "psychologist" && ownSlot)) && (
                        <button className="danger-button" onClick={() => deleteSlot(slot.id)}>
                          Удалить
                        </button>
                      )}
                      {bookedByMe && <span className="status-pill">Вы записаны</span>}
                    </article>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
