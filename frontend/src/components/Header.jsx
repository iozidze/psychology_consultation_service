import { useEffect, useState } from "react";
import { apiRequest } from "../api.js";

const roleLabels = {
  admin: "Администратор",
  psychologist: "Психолог",
  client: "Клиент",
};

export default function Header({ user, token, activeTab, onTabChange, onLogout }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      const value = query.trim();
      if (!value) {
        setResults([]);
        setError("");
        return;
      }
      try {
        const data = await apiRequest(`/users/search?q=${encodeURIComponent(value)}`, { token });
        if (!controller.signal.aborted) {
          setResults(data);
          setError("");
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err.message);
          setResults([]);
        }
      }
    }, 250);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [query, token]);

  const tabs =
    user.role === "admin"
      ? [{ id: "admin", label: "Администрирование" }]
      : [
          { id: "calendar", label: "Календарь" },
          { id: "profile", label: "Профиль" },
          { id: "notes", label: "Рекомендации и заметки" },
        ];

  return (
    <header className="app-header">
      <div className="top-line">
        <div>
          <p className="eyebrow">Онлайн-консультации</p>
          <h1>Психолог рядом</h1>
        </div>
        <div className="user-chip">
          <span>{roleLabels[user.role]}</span>
          <strong>@{user.username}</strong>
          <button type="button" className="ghost-button" onClick={onLogout}>
            Выйти
          </button>
        </div>
      </div>

      <div className="search-wrap">
        <input
          className="global-search"
          placeholder="Поиск по нику, а для психологов ещё и по настоящему имени"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        {(results.length > 0 || error) && (
          <div className="search-results">
            {error && <div className="error compact">{error}</div>}
            {results.map((result) => (
              <div key={result.id} className="search-result">
                <div>
                  <strong>@{result.username}</strong>
                  <span>{roleLabels[result.role]}</span>
                </div>
                {result.full_name && <p>{result.full_name}</p>}
                {result.specialization && <p>{result.specialization}</p>}
              </div>
            ))}
          </div>
        )}
      </div>

      <nav className="tabs" aria-label="Разделы">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={activeTab === tab.id ? "active" : ""}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
