import { useEffect, useState } from "react";
import { apiRequest } from "../api.js";

function formatDate(value) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function Notes({ user, token, onUserChange }) {
  const [notes, setNotes] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [clients, setClients] = useState([]);
  const [noteForm, setNoteForm] = useState({ client_id: "", text: "" });
  const [recommendationForm, setRecommendationForm] = useState({ client_id: "", text: "" });
  const [reviewForm, setReviewForm] = useState({ psychologist_id: "", rating: 5, text: "" });
  const [editingNote, setEditingNote] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadData = async () => {
    try {
      const [loadedNotes, loadedRecommendations] = await Promise.all([
        apiRequest("/notes/", { token }),
        apiRequest("/notes/recommendations", { token }),
      ]);
      setNotes(loadedNotes);
      setRecommendations(loadedRecommendations);
      if (user.role === "psychologist") {
        setClients(await apiRequest("/users/clients", { token }));
      }
      setError("");
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const createNote = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await apiRequest("/notes/", {
        method: "POST",
        token,
        body: {
          client_id: noteForm.client_id ? Number(noteForm.client_id) : undefined,
          text: noteForm.text,
        },
      });
      setNoteForm({ client_id: "", text: "" });
      setMessage("Заметка сохранена");
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const updateNote = async (noteId) => {
    try {
      await apiRequest(`/notes/${noteId}`, {
        method: "PUT",
        token,
        body: { text: editingNote.text },
      });
      setEditingNote(null);
      setMessage("Заметка обновлена");
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const createRecommendation = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await apiRequest("/notes/recommendations", {
        method: "POST",
        token,
        body: {
          client_id: Number(recommendationForm.client_id),
          text: recommendationForm.text,
        },
      });
      setRecommendationForm({ client_id: "", text: "" });
      setMessage("Рекомендация отправлена клиенту");
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const sendReview = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await apiRequest("/notes/reviews", {
        method: "POST",
        token,
        body: {
          psychologist_id: Number(reviewForm.psychologist_id),
          rating: Number(reviewForm.rating),
          text: reviewForm.text,
        },
      });
      const updatedUser = await apiRequest("/users/me", { token });
      onUserChange(updatedUser);
      setReviewForm({ psychologist_id: "", rating: 5, text: "" });
      setMessage("Отзыв отправлен");
    } catch (err) {
      setError(err.message);
    }
  };

  const clientOptions = clients.map((client) => (
    <option value={client.id} key={client.id}>
      @{client.username}
    </option>
  ));

  return (
    <section className="notes-layout">
      {error && <div className="error wide">{error}</div>}
      {message && <div className="success wide">{message}</div>}

      {user.role === "psychologist" && (
        <>
          <form className="panel form-panel" onSubmit={createNote}>
            <div>
              <p className="eyebrow">Рабочие записи</p>
              <h2>Добавить запись</h2>
            </div>
            <label>
              Клиент
              <select value={noteForm.client_id} onChange={(event) => setNoteForm({ ...noteForm, client_id: event.target.value })} required>
                <option value="">Выберите клиента</option>
                {clientOptions}
              </select>
            </label>
            <label>
              Текст заметки
              <textarea value={noteForm.text} onChange={(event) => setNoteForm({ ...noteForm, text: event.target.value })} rows="6" required />
            </label>
            <button className="primary-button">Сохранить запись</button>
          </form>

          <form className="panel form-panel" onSubmit={createRecommendation}>
            <div>
              <p className="eyebrow">Рекомендации</p>
              <h2>Добавить рекомендацию</h2>
            </div>
            <label>
              Клиент
              <select
                value={recommendationForm.client_id}
                onChange={(event) => setRecommendationForm({ ...recommendationForm, client_id: event.target.value })}
                required
              >
                <option value="">Выберите клиента</option>
                {clientOptions}
              </select>
            </label>
            <label>
              Рекомендация
              <textarea
                value={recommendationForm.text}
                onChange={(event) => setRecommendationForm({ ...recommendationForm, text: event.target.value })}
                rows="6"
                required
              />
            </label>
            <button className="primary-button">Отправить клиенту</button>
          </form>
        </>
      )}

      {user.role === "client" && (
        <>
          <form className="panel form-panel" onSubmit={createNote}>
            <div>
              <p className="eyebrow">Личные заметки</p>
              <h2>Добавить заметку</h2>
            </div>
            <label>
              Текст заметки
              <textarea value={noteForm.text} onChange={(event) => setNoteForm({ ...noteForm, text: event.target.value })} rows="6" required />
            </label>
            <button className="primary-button">Сохранить</button>
          </form>

          <form className="panel form-panel" onSubmit={sendReview}>
            <div>
              <p className="eyebrow">Обратная связь</p>
              <h2>Отзыв психологу</h2>
            </div>
            <label>
              Психолог
              <select
                value={reviewForm.psychologist_id}
                onChange={(event) => setReviewForm({ ...reviewForm, psychologist_id: event.target.value })}
                required
              >
                <option value="">Выберите из рекомендаций</option>
                {recommendations.map((item) => (
                  <option value={item.psychologist_id} key={item.id}>
                    @{item.psychologist_username}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Оценка
              <input
                type="number"
                min="1"
                max="5"
                value={reviewForm.rating}
                onChange={(event) => setReviewForm({ ...reviewForm, rating: event.target.value })}
              />
            </label>
            <label>
              Текст отзыва
              <textarea value={reviewForm.text} onChange={(event) => setReviewForm({ ...reviewForm, text: event.target.value })} rows="4" />
            </label>
            <button className="primary-button">Отправить отзыв</button>
          </form>
        </>
      )}

      <div className="panel records-panel">
        <div>
          <p className="eyebrow">{user.role === "client" ? "Ваши рекомендации" : "Сохранённые записи"}</p>
          <h2>{user.role === "client" ? "Рекомендации психологов" : "Заметки по клиентам"}</h2>
        </div>

        {user.role === "client" && recommendations.length === 0 && <div className="empty">Пока нет рекомендаций</div>}

        {user.role === "client" && recommendations.map((item) => (
          <article className="record-card" key={item.id}>
            <strong>@{item.psychologist_username}</strong>
            {item.psychologist_full_name && <span>{item.psychologist_full_name}</span>}
            <p>{item.text}</p>
          </article>
        ))}

        {notes.length === 0 && <div className="empty">Пока нет заметок</div>}

        {notes.map((note) => (
          <article className="record-card" key={note.id}>
            <div className="record-head">
              <strong>{user.role === "psychologist" ? `Клиент @${note.client_username}` : "Личная заметка"}</strong>
              <button className="ghost-button" type="button" onClick={() => setEditingNote(note)}>
                Редактировать
              </button>
            </div>
            {user.role === "client" && <span className="note-date">Создана: {formatDate(note.created_at)}</span>}
            {editingNote?.id === note.id ? (
              <div className="edit-box">
                <textarea value={editingNote.text} onChange={(event) => setEditingNote({ ...editingNote, text: event.target.value })} rows="5" />
                <button className="primary-button" onClick={() => updateNote(note.id)}>
                  Сохранить
                </button>
              </div>
            ) : (
              <p>{note.text}</p>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
