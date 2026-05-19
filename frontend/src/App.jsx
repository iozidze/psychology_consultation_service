import { useEffect, useState } from "react";
import { apiRequest } from "./api.js";
import AdminPanel from "./components/AdminPanel.jsx";
import AuthModal from "./components/AuthModal.jsx";
import Calendar from "./components/Calendar.jsx";
import Header from "./components/Header.jsx";
import Notes from "./components/Notes.jsx";
import Profile from "./components/Profile.jsx";

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("calendar");
  const [booting, setBooting] = useState(Boolean(token));

  useEffect(() => {
    if (!token) {
      setBooting(false);
      return;
    }
    apiRequest("/users/me", { token })
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("token");
        setToken(null);
      })
      .finally(() => setBooting(false));
  }, [token]);

  useEffect(() => {
    if (user?.role === "admin" && activeTab !== "admin") {
      setActiveTab("admin");
    }
  }, [user, activeTab]);

  const handleAuth = (data) => {
    localStorage.setItem("token", data.access_token);
    setToken(data.access_token);
    setUser(data.user);
    setActiveTab(data.user.role === "admin" ? "admin" : "calendar");
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
    setActiveTab("calendar");
  };

  if (booting) {
    return <div className="app-shell loading-screen">Загружаем сервис...</div>;
  }

  return (
    <div className="app-shell">
      {!user && <AuthModal onAuth={handleAuth} />}

      {user && (
        <>
          <Header user={user} token={token} activeTab={activeTab} onTabChange={setActiveTab} onLogout={logout} />
          <main>
            {activeTab === "calendar" && <Calendar user={user} token={token} />}
            {activeTab === "profile" && <Profile user={user} token={token} onUserChange={setUser} />}
            {activeTab === "notes" && <Notes user={user} token={token} onUserChange={setUser} />}
            {activeTab === "admin" && user.role === "admin" && <AdminPanel token={token} />}
          </main>
        </>
      )}
    </div>
  );
}
